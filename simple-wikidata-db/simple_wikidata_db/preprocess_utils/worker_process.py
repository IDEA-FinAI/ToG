from collections import defaultdict
from multiprocessing import Queue

# properties which encode some alias/name
import ujson

ALIAS_PROPERTIES = {
    "P138",
    "P734",
    "P735",
    "P742",
    "P1448",
    "P1449",
    "P1477",
    "P1533",
    "P1549",
    "P1559",
    "P1560",
    "P1635",
    "P1705",
    "P1782",
    "P1785",
    "P1786",
    "P1787",
    "P1810",
    "P1813",
    "P1814",
    "P1888",
    "P1950",
    "P2358",
    "P2359",
    "PP2365",
    "P2366",
    "P2521",
    "P2562",
    "P2976",
    "PP3321",
    "P4239",
    "P4284",
    "P4970",
    "P5056",
    "P5278",
    "PP6978",
    "P7383",
}

# data types in wikidata dump which we ignore
IGNORE = {
    "wikibase-lexeme",
    "musical-notation",
    "globe-coordinate",
    "commonsMedia",
    "geo-shape",
    "wikibase-sense",
    "wikibase-property",
    "math",
    "tabular-data",
}


def process_mainsnak(data, language_id):
    datatype = data["datatype"]
    if datatype == "string":
        return data["datavalue"]["value"]
    elif datatype == "monolingualtext":
        if data["datavalue"]["value"]["language"] == language_id:
            return data["datavalue"]["value"]["text"]
    elif datatype == "quantity":
        return data["datavalue"]["value"]["amount"]
    elif datatype == "time":
        return data["datavalue"]["value"]["time"]
    elif datatype == "wikibase-item":
        return data["datavalue"]["value"]["id"]
    elif datatype == "external-id":
        return data["datavalue"]["value"]
    elif datatype == "url":
        return data["datavalue"]["value"]

    # Ignore all other triples
    elif datatype in IGNORE:
        return None
    else:
        return None
    return None


def process_json(obj, language_id="en"):
    out_data = defaultdict(list)
    id = obj["id"]  # The canonical ID of the entity.
    # skip properties
    if obj["type"] == "property":
        out_data["plabels"].append(
            {"pid": id, "label": obj["labels"][language_id]["value"]}
        )
        return dict(out_data)
    # extract labels
    if language_id in obj["labels"]:
        label = obj["labels"][language_id]["value"]
        out_data["labels"].append({"qid": id, "label": label})
        out_data["aliases"].append({"qid": id, "alias": label})

    # extract description
    if language_id in obj["descriptions"]:
        description = obj["descriptions"][language_id]["value"]
        out_data["descriptions"].append(
            {
                "qid": id,
                "description": description,
            }
        )

    # extract aliases
    if language_id in obj["aliases"]:
        for alias in obj["aliases"][language_id]:
            out_data["aliases"].append(
                {
                    "qid": id,
                    "alias": alias["value"],
                }
            )

    # extract english wikipedia sitelink -- we just add this to the external links table
    if f"{language_id}wiki" in obj["sitelinks"]:
        sitelink = obj["sitelinks"][f"{language_id}wiki"]["title"]
        out_data["wikipedia_links"].append({"qid": id, "wiki_title": sitelink})

    # extract claims and qualifiers
    for property_id in obj["claims"]:
        for claim in obj["claims"][property_id]:
            if not claim["mainsnak"]["snaktype"] == "value":
                continue
            claim_id = claim["id"]
            datatype = claim["mainsnak"]["datatype"]
            value = process_mainsnak(claim["mainsnak"], language_id)

            if value is None:
                continue

            if datatype == "wikibase-item":
                out_data["entity_rels"].append(
                    {
                        "claim_id": claim_id,
                        "qid": id,
                        "property_id": property_id,
                        "value": value,
                    }
                )
            elif datatype == "external-id":
                out_data["external_ids"].append(
                    {
                        "claim_id": claim_id,
                        "qid": id,
                        "property_id": property_id,
                        "value": value,
                    }
                )
            else:
                out_data["entity_values"].append(
                    {
                        "claim_id": claim_id,
                        "qid": id,
                        "property_id": property_id,
                        "value": value,
                    }
                )
                if property_id in ALIAS_PROPERTIES:
                    out_data["aliases"].append(
                        {
                            "qid": id,
                            "alias": value,
                        }
                    )

            # get qualifiers
            if "qualifiers" in claim:
                for qualifier_property in claim["qualifiers"]:
                    for qualifier in claim["qualifiers"][qualifier_property]:
                        if not qualifier["snaktype"] == "value":
                            continue
                        qualifier_id = qualifier["hash"]
                        value = process_mainsnak(qualifier, language_id)
                        if value is None:
                            continue
                        out_data["qualifiers"].append(
                            {
                                "qualifier_id": qualifier_id,
                                "claim_id": claim_id,
                                "property_id": qualifier_property,
                                "value": value,
                            }
                        )

    return dict(out_data)


def process_data(language_id: str, work_queue: Queue, out_queue: Queue):
    while True:
        json_obj = work_queue.get()
        if json_obj is None:
            break
        if len(json_obj) == 0:
            continue
        out_queue.put(process_json(ujson.loads(json_obj), language_id))
    return

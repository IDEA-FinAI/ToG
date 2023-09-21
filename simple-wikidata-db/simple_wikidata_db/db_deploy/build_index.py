from functools import partial
import os
import pickle
from collections import defaultdict
from multiprocessing import Pool
from numpy import require
from tqdm import tqdm
import math
from dataclasses import dataclass
import ujson as json
from simple_wikidata_db.db_deploy.utils import (
    a_factory,
    Entity,
    Relation,
    get_batch_files,
    jsonl_generator,
    read_relation_label,
    read_entity_label,
)
import typing as tp


def read_relation_entities(filename):
    relation_entities = []
    for item in jsonl_generator(filename):
        relation_entities.append(
            {
                "head_qid": item["qid"],
                "pid": item["property_id"],
                "tail_qid": item["value"],
            }
        )
    return relation_entities


def read_tail_values(filename):
    relation_entities = []
    for item in jsonl_generator(filename):
        relation_entities.append(
            {
                "head_qid": item["qid"],
                "pid": item["property_id"],
                "tail_value": item["value"],
            }
        )
    return relation_entities


def read_external_ids(filename):
    relation_entities = []
    for item in jsonl_generator(filename):
        relation_entities.append(
            {
                "qid": item["qid"],
                "pid": item["property_id"],
                "value": item["value"],
            }
        )
    return relation_entities


from collections import defaultdict
from typing import DefaultDict


def merge_defaultdicts(
    dd1: DefaultDict[str, list], dd2: DefaultDict[str, list]
) -> DefaultDict[str, list]:
    # Create a new defaultdict to hold the merged results
    merged_dict = defaultdict(list, dd1)

    # Merge dd1 and dd2
    for key, val in dd2.items():
        merged_dict[key].extend(val)

    return merged_dict


def filter_value(
    dict_list: tp.List[tp.Dict],
    key: str,
) -> tp.List[tp.Dict]:
    ret_list = []
    for dict_item in tqdm(dict_list, desc='filter_value iter over dict_list'):
        if key in dict_item:
            ret_list.append(dict_item[key])
    # Flatten the list
    ret_list = [item for sublist in ret_list for item in sublist]
    return key, ret_list


def main(args):
    os.makedirs(args.output_dir, exist_ok=True)
    data_dir = args.input_dir
    num_chunks = args.num_chunks  # adjust as needed
    pool = Pool(processes=args.num_workers)  # adjust as needed

    files_index = {
        "labels": get_batch_files(os.path.join(data_dir, "labels")),
        "descriptions": get_batch_files(os.path.join(data_dir, "descriptions")),
        "aliases": get_batch_files(os.path.join(data_dir, "aliases")),
        "entity_rels": get_batch_files(os.path.join(data_dir, "entity_rels")),
        "external_ids": get_batch_files(os.path.join(data_dir, "external_ids")),
        "entity_values": get_batch_files(
            os.path.join(data_dir, "entity_values")
        ),
        "qualifiers": get_batch_files(os.path.join(data_dir, "qualifiers")),
        "wikipedia_links": get_batch_files(
            os.path.join(data_dir, "wikipedia_links")
        ),
        "plabels": get_batch_files(os.path.join(data_dir, "plabels")),
    }
    chunk_size_entity_rels = math.ceil(
        len(files_index["entity_rels"]) / num_chunks
    )
    chunk_size_entity_values = math.ceil(
        len(files_index["entity_values"]) / num_chunks
    )
    chunk_size_external_ids = math.ceil(
        len(files_index["external_ids"]) / num_chunks
    )

    # QID/PID <=> Name mapping
    qid_to_name = {}
    name_to_qid = {}
    name_to_qid_list = []
    pid_to_name = {}
    name_to_pid = {}
    name_to_pid_list = []
    print(f"args.chunk_idx: {args.chunk_idx}")

    # Step 1: Read Entity label <=> QID mapping
    print("Reading entity labels ...")
    for output in tqdm(
        pool.imap_unordered(
            read_entity_label, files_index["labels"], chunksize=1
        ),
    ):
        qid_to_name.update(output[0])
    #     name_to_qid_list.append(output[1])

    # all_entity_names = set()
    # for d in name_to_qid_list:
    #     all_entity_names.update(d.keys())
    # counter = 0
    # for name, qids in tqdm(
    #     pool.imap_unordered(
    #         partial(filter_value, dict_list=name_to_qid_list),
    #         all_entity_names,
    #         chunksize=1,
    #     ),
    # ):
    #     name_to_qid[name] = qids
    #     if counter < 5:
    #         print(f"{name}: {qids}")
    #         counter += 1

    # Step 2: Read Relation label <=> PID mapping
    print("Reading relation labels ...")
    for output in tqdm(
        pool.imap_unordered(
            read_relation_label, files_index["plabels"], chunksize=1
        ),
    ):
        pid_to_name.update(output[0])
    #     name_to_pid_list.append(output[1])
    
    # all_relation_names = set.intersection(*map(set, name_to_pid_list))
    # counter = 0
    # for name, pids in tqdm(
    #     pool.imap_unordered(
    #         partial(filter_value, dict_list=name_to_pid_list),
    #         all_relation_names,
    #         chunksize=1,
    #     ),
    # ):
    #     name_to_pid[name] = pids
    #     if counter < 5:
    #         print(f"{name}: {pids}")
    #         counter += 1

    # missing_qids = []
    # missing_pids = []

    # Step 3: Read entity_rels, entity_values, and external_ids
    for i in range(num_chunks):
        if args.chunk_idx != -1 and i != args.chunk_idx:
            continue
        start = i * chunk_size_entity_rels
        end = start + chunk_size_entity_rels
        chunk_files = files_index["entity_rels"][start:end]

        relations_linked_to_entities = defaultdict(a_factory)
        entities_related_to_relent_pair = defaultdict(a_factory)
        tail_values = defaultdict(list)

        print(f"Processing `entity_rels` of chunk {i+1} ...")
        for output in tqdm(
            pool.imap_unordered(
                read_relation_entities,
                chunk_files,
                chunksize=1,
            )
        ):
            for item in output:
                # if item["pid"] not in pid_to_name:
                #     missing_pids.append(item["pid"])
                # if item["tail_qid"] not in qid_to_name:
                #     missing_qids.append(item["tail_qid"])
                rel = Relation(
                    pid=item["pid"],
                    label=pid_to_name.get(item["pid"], "N/A"),
                )
                relations_linked_to_entities[item["head_qid"]]["head"].append(
                    rel
                )
                relations_linked_to_entities[item["tail_qid"]]["tail"].append(
                    rel
                )

                entities_related_to_relent_pair[
                    f'{item["head_qid"]}@{item["pid"]}'
                ]["tail"].append(
                    Entity(
                        qid=item["tail_qid"],
                        label=qid_to_name.get(item["tail_qid"], "N/A"),
                    )
                )
                entities_related_to_relent_pair[
                    f'{item["tail_qid"]}@{item["pid"]}'
                ]["head"].append(
                    Entity(
                        qid=item["head_qid"],
                        label=qid_to_name.get(item["head_qid"], "N/A"),
                    )
                )

        print(f"Processing `entity_values` of chunk {i+1} ...")
        start = i * chunk_size_entity_values
        end = start + chunk_size_entity_values
        chunk_files = files_index["entity_values"][start:end]
        for output in tqdm(
            pool.imap_unordered(
                read_tail_values,
                chunk_files,
                chunksize=1,
            )
        ):
            for item in output:
                # if item["pid"] not in pid_to_name:
                #     missing_pids.append(item["pid"])
                relations_linked_to_entities[item["head_qid"]]["head"].append(
                    Relation(
                        pid=item["pid"],
                        label=pid_to_name.get(item["pid"], "N/A"),
                    )
                )
                tail_values[f'{item["head_qid"]}@{item["pid"]}'].append(
                    item["tail_value"]
                )

        external_ids = defaultdict(list)
        mid_to_qid = defaultdict(list)
        print(f"Processing `external_ids` of chunk {i+1} ...")
        start = i * chunk_size_external_ids
        end = start + chunk_size_external_ids
        chunk_files = files_index["external_ids"][start:end]
        for output in tqdm(
            pool.imap_unordered(read_external_ids, chunk_files, chunksize=1)
        ):
            for item in output:
                external_ids[f'{item["qid"]}@{item["pid"]}'].append(
                    item["value"]
                )
                mid_to_qid[f'{item["value"]}'].append(item["qid"])

        # Dump 3 index files
        with open(
            f"{args.output_dir}/relation_entities_chunk_{i+1}.pickle", "wb"
        ) as handle:
            pickle.dump(
                relations_linked_to_entities,
                handle,
                protocol=pickle.HIGHEST_PROTOCOL,
            )
        with open(
            f"{args.output_dir}/tail_entities_chunk_{i+1}.pickle", "wb"
        ) as handle:
            pickle.dump(
                entities_related_to_relent_pair,
                handle,
                protocol=pickle.HIGHEST_PROTOCOL,
            )

        with open(
            f"{args.output_dir}/tail_values_chunk_{i+1}.pickle", "wb"
        ) as handle:
            pickle.dump(tail_values, handle, protocol=pickle.HIGHEST_PROTOCOL)

        with open(
            f"{args.output_dir}/external_ids_chunk_{i+1}.pickle", "wb"
        ) as handle:
            pickle.dump(external_ids, handle, protocol=pickle.HIGHEST_PROTOCOL)
            
        with open(
            f"{args.output_dir}/mid_to_qid_chunk_{i+1}.pickle", "wb"
        ) as handle:
            pickle.dump(mid_to_qid, handle, protocol=pickle.HIGHEST_PROTOCOL)

        # print(
        #     f"Missing QIDs: {len(missing_qids)}, total: {len(qid_to_name)}, ratio: {len(missing_qids)/len(qid_to_name)}"
        # )
        # print(
        #     f"Missing PIDs: {len(missing_pids)}, total: {len(pid_to_name)}, ratio: {len(missing_pids)/len(pid_to_name)}"
        # )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="Preprocessed Wikidata dumpfile directory",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        required=True,
        help="Output directory",
    )
    parser.add_argument("--num_chunks", type=int, default=5)
    parser.add_argument("--num_workers", type=int, default=400)
    parser.add_argument("--chunk_idx", type=int, default=-1)

    args = parser.parse_args()
    main(args)

import itertools
import xmlrpc.client
import typing as tp
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from simple_wikidata_db.db_deploy.utils import Entity, Relation, a_factory
import requests
from bs4 import BeautifulSoup


class WikidataQueryClient:
    def __init__(self, url: str):
        self.url = url
        self.server = xmlrpc.client.ServerProxy(url)

    def label2qid(self, label: str) -> str:
        return self.server.label2qid(label)

    def label2pid(self, label: str) -> str:
        return self.server.label2pid(label)

    def pid2label(self, pid: str) -> str:
        return self.server.pid2label(pid)

    def qid2label(self, qid: str) -> str:
        return self.server.qid2label(qid)

    def get_all_relations_of_an_entity(
        self, entity_qid: str
    ) -> tp.Dict[str, tp.List]:
        return self.server.get_all_relations_of_an_entity(entity_qid)

    def get_tail_entities_given_head_and_relation(
        self, head_qid: str, relation_pid: str
    ) -> tp.Dict[str, tp.List]:
        return self.server.get_tail_entities_given_head_and_relation(
            head_qid, relation_pid
        )

    def get_tail_values_given_head_and_relation(
        self, head_qid: str, relation_pid: str
    ) -> tp.List[str]:
        return self.server.get_tail_values_given_head_and_relation(
            head_qid, relation_pid
        )

    def get_external_id_given_head_and_relation(
        self, head_qid: str, relation_pid: str
    ) -> tp.List[str]:
        return self.server.get_external_id_given_head_and_relation(
            head_qid, relation_pid
        )

    def get_wikipedia_page(self, qid: str, section: str = None) -> str:
        wikipedia_url = self.server.get_wikipedia_link(qid)
        if wikipedia_url == "Not Found!":
            return "Not Found!"
        else:
            response = requests.get(wikipedia_url)
            if response.status_code != 200:
                raise Exception(f"Failed to retrieve page: {wikipedia_url}")

            soup = BeautifulSoup(response.content, "html.parser")
            content_div = soup.find("div", {"id": "bodyContent"})

            # Remove script and style elements
            for script_or_style in content_div.find_all(["script", "style"]):
                script_or_style.decompose()

            if section:
                header = content_div.find(
                    lambda tag: tag.name == "h2" and section in tag.get_text()
                )
                if header:
                    content = ""
                    for sibling in header.find_next_siblings():
                        if sibling.name == "h2":
                            break
                        content += sibling.get_text()
                    return content.strip()
                else:
                    # If the specific section is not found, return an empty string or a message.
                    return f"Section '{section}' not found."

            # Fetch the header summary (before the first h2)
            summary_content = ""
            for element in content_div.find_all(recursive=False):
                if element.name == "h2":
                    break
                summary_content += element.get_text()

            return summary_content.strip()

    def mid2qid(self, mid: str) -> str:
        return self.server.mid2qid(mid)


import time
import typing as tp
from concurrent.futures import ThreadPoolExecutor


class MultiServerWikidataQueryClient:
    def __init__(self, urls: tp.List[str]):
        self.clients = [WikidataQueryClient(url) for url in urls]
        self.executor = ThreadPoolExecutor(max_workers=len(urls))
        # test connections
        start_time = time.perf_counter()
        self.test_connections()
        end_time = time.perf_counter()
        print(f"Connection testing took {end_time - start_time} seconds")

    def test_connections(self):
        def test_url(client):
            try:
                # Check if server provides the system.listMethods function.
                client.server.system.listMethods()
                return True
            except Exception as e:
                print(f"Failed to connect to {client.url}. Error: {str(e)}")
                return False

        start_time = time.perf_counter()
        futures = [
            self.executor.submit(test_url, client) for client in self.clients
        ]
        results = [f.result() for f in futures]
        end_time = time.perf_counter()
        # print(f"Testing connections took {end_time - start_time} seconds")
        # Remove clients that failed to connect
        self.clients = [
            client for client, result in zip(self.clients, results) if result
        ]
        if not self.clients:
            raise Exception("Failed to connect to all URLs")

    def query_all(self, method, *args):
        start_time = time.perf_counter()
        futures = [
            self.executor.submit(getattr(client, method), *args)
            for client in self.clients
        ]
        # Retrieve results and filter out 'Not Found!'
        is_dict_return = method in [
            "get_all_relations_of_an_entity",
            "get_tail_entities_given_head_and_relation",
        ]
        results = [f.result() for f in futures]
        end_time = time.perf_counter()
        # print(f"HTTP Queries took {end_time - start_time} seconds")

        start_time = time.perf_counter()
        real_results = (
            set() if not is_dict_return else {"head": [], "tail": []}
        )
        for res in results:
            if isinstance(res, str) and res == "Not Found!":
                continue
            elif isinstance(res, tp.List):
                if len(res) == 0:
                    continue
                if isinstance(res[0], tp.List):
                    res_flattened = itertools.chain(*res)
                    real_results.update(res_flattened)
                    continue
                real_results.update(res)
            elif is_dict_return:
                real_results["head"].extend(res["head"])
                real_results["tail"].extend(res["tail"])
            else:
                real_results.add(res)
        end_time = time.perf_counter()
        # print(f"Querying all took {end_time - start_time} seconds")

        return real_results if len(real_results) > 0 else "Not Found!"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--addr_list",
        type=str,
        required=True,
        help="path to server address list",
    )
    args = parser.parse_args()

    with open(args.addr_list, "r") as f:
        server_addrs = f.readlines()
        server_addrs = [addr.strip() for addr in server_addrs]
    print(f"Server addresses: {server_addrs}")
    client = MultiServerWikidataQueryClient(server_addrs)
    print(
        f'MSFT\'s ticker code is  {client.query_all("get_tail_values_given_head_and_relation","Q2283","P249",)}'
    )
    # exit(0)
    exchange_qids = {
        "NYSE": "Q13677",
        "NASDAQ": "Q82059",
        "XSHG": "Q739514",
        "XSHE": "Q517750",
        "AMEX": "Q846626",
        "Euronext Paris": "Q2385849",
        "HKEX": "Q496672",
        "Tokyo": "Q217475",
        "Osaka": "Q1320224",
        "London": "Q171240",
    }

    for xchg in exchange_qids:
        xchg_name = xchg
        stocks = client.query_all(
            "get_tail_entities_given_head_and_relation",
            exchange_qids[xchg_name],
            "P414",
        )
        stocks = stocks["head"]

        acs = {}
        for stock_record in tqdm(stocks):
            ticker_id = client.query_all(
                "get_tail_values_given_head_and_relation",
                stock_record["qid"],
                "P249",
            )
            acs[stock_record["qid"]] = {
                "label": stock_record["label"],
                "ticker": ticker_id,
            }
        import yaml

        with open(f"{xchg_name}.yaml", "w") as f:
            yaml.safe_dump(acs, f)

    # am = {}
    # for s in stocks:
    #     am[s] = client.query_all("qid2label", s)

    # import yaml
    # with open(f"{xchg_name}.yaml", "w") as f:
    #     yaml.safe_dump(am, f)

    # print(client.query_all("get_all_relations_of_an_entity", "Q312",))
    # print(
    #     f'MSFT\'s Freebase MID is {client.query_all("get_external_id_given_head_and_relation", "Q2283", "P646")}'
    # )
    # print(
    #     f'MID /m/0k8z corresponds to QID {client.query_all("mid2qid", "/m/0k8z")}'
    # )
    # print(client.query_all("label2pid", 'spouse'))  # P26

    # print(f'Carrollton => {client.query_all("label2qid", "Carrollton")}')
    # print(client.query_all("label2pid", "crosses"))

    # print(client.query_all(
    #         "get_tail_entities_given_head_and_relation", "Q6792298", "P106"
    #     )
    # )
    # print(
    #     client.query_all(
    #         "get_tail_entities_given_head_and_relation", "Q42869", "P161"
    #     )
    # )  # (Q507306, 'NASDAQ-100'), (Q180816, DJIA), ...
    # print(
    #     client.query_all(
    #         "get_tail_values_given_head_and_relation", "Q2283", "P2139"
    #     )
    # )  # MS revenue

    # # Speed profiling
    # for i in tqdm(range(1000)):
    #     # print(client.query_all("label2qid", "Microsoft"))  # Q2283
    #     client.query_all("label2qid", "Microsoft")
    #     # print(client.query_all("qid2label", "Q2283"))  # Microsoft
    #     client.query_all("qid2label", "Q2283")
    #     # print(
    #     client.query_all("get_all_relations_of_an_entity", "Q2283")
    #     # )  # (P31, 'instance of'), (P361, 'part of'), ...
    #     # print(
    #     client.query_all(
    #         "get_tail_entities_given_head_and_relation", "Q2283", "P361"
    #     )
    #     # )  # (Q507306, 'NASDAQ-100'), (Q180816, DJIA), ...
    #     # print(
    #     client.query_all(
    #         "get_tail_values_given_head_and_relation", "Q2283", "P2139"
    #     )
    #     # )  # MS revenue

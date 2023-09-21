import os
import pickle
import typing as tp
from collections import defaultdict
from dataclasses import dataclass
from functools import partial
from multiprocessing import Pool
from xmlrpc.server import SimpleXMLRPCRequestHandler, SimpleXMLRPCServer
from numpy import require
from sqlalchemy import true
from simple_wikidata_db.db_deploy.utils import (
    Entity,
    Relation,
    a_factory,
    jsonl_generator,
    get_batch_files,
    read_entity_label,
    read_relation_label,
)
import ujson as json
from tqdm import tqdm
import itertools


def merge_list_of_list(dd1, dd2):
    """
    Optimized function to merge two defaultdict(list) instances.
    For common keys, lists will be concatenated.
    """
    merged_dd = dd1

    # Using dictionary comprehension to merge
    for key in dd2.keys():
        merged_dd[key].append(dd2[key])

    return merged_dd


class WikidataQueryServer:
    def __init__(
        self,
        chunk_number: int,
        data_dir: str,
        num_workers: int = 400,
    ):
        self.num_workers = num_workers
        self.pool = Pool(processes=self.num_workers)

        self.files_index = {
            "labels": get_batch_files(os.path.join(data_dir, "labels")),
            "plabels": get_batch_files(os.path.join(data_dir, "plabels")),
        }

        self.qid_to_name = {}
        self.name_to_qid = defaultdict(list)
        self.pid_to_name = {}
        self.name_to_pid = defaultdict(list)
        print("Reading relation labels ...")
        for output in tqdm(
            self.pool.imap_unordered(
                read_relation_label, self.files_index["plabels"], chunksize=1
            )
        ):
            self.pid_to_name.update(output[0])
            self.name_to_pid = merge_list_of_list(self.name_to_pid, output[1])
        for k, v in self.name_to_pid.items():
            self.name_to_pid[k] = list(itertools.chain(*v))

        print("Reading entity labels ...")
        for output in tqdm(
            self.pool.imap_unordered(
                read_entity_label, self.files_index["labels"], chunksize=1
            )
        ):
            self.qid_to_name.update(output[0])
            self.name_to_qid = merge_list_of_list(self.name_to_qid, output[1])

        for k, v in self.name_to_qid.items():
            self.name_to_qid[k] = list(itertools.chain(*v))

        print("Reading links ...")
        chunk_number = chunk_number + 1
        print(
            f"Reading {args.data_dir}/indices/relation_entities_chunk_{chunk_number}.pickle"
        )
        with open(
            f"{args.data_dir}/indices/relation_entities_chunk_{chunk_number}.pickle",
            "rb",
        ) as handle:
            self.relation_entities = pickle.load(handle)
        print(
            f"Reading {args.data_dir}/indices/tail_entities_chunk_{chunk_number}.pickle"
        )
        with open(
            f"{args.data_dir}/indices/tail_entities_chunk_{chunk_number}.pickle",
            "rb",
        ) as handle:
            self.tail_entities = pickle.load(handle)
        print(
            f"Reading {args.data_dir}/indices/tail_values_chunk_{chunk_number}.pickle"
        )
        with open(
            f"{args.data_dir}/indices/tail_values_chunk_{chunk_number}.pickle",
            "rb",
        ) as handle:
            self.tail_values = pickle.load(handle)
        print(
            f"Reading {args.data_dir}/indices/external_ids_chunk_{chunk_number}.pickle"
        )
        with open(
            f"{args.data_dir}/indices/external_ids_chunk_{chunk_number}.pickle",
            "rb",
        ) as handle:
            self.external_ids = pickle.load(handle)
        with open(
            f"{args.data_dir}/indices/mid_to_qid_chunk_{chunk_number}.pickle",
            "rb",
        ) as handle:
            self.mid_to_qid = pickle.load(handle)

        # See the number of conflict names by making differences in length
        dup_entity_names = len(self.qid_to_name) - len(self.name_to_qid)
        print(
            f"Total entities = {len(self.qid_to_name)}, duplicate names = {dup_entity_names}"
        )

    def label2qid(self, label: str) -> tp.List[Entity]:
        return self.name_to_qid.get(label, "Not Found!")

    def label2pid(self, label: str) -> tp.List[Relation]:
        return self.name_to_pid.get(label, "Not Found!")

    def qid2label(self, qid: str) -> tp.List[Entity]:
        return self.qid_to_name.get(qid, "Not Found!")

    def pid2label(self, pid: str) -> tp.List[Relation]:
        return self.pid_to_name.get(pid, "Not Found!")

    def mid2qid(self, mid: str) -> tp.List[str]:
        return self.mid_to_qid.get(mid, "Not Found!")

    def get_all_relations_of_an_entity(
        self, entity_qid: str
    ) -> tp.Dict[str, tp.List[Relation]]:
        try:
            return self.relation_entities[entity_qid]
        except KeyError:
            return "Not Found!"

    def get_tail_entities_given_head_and_relation(
        self, head_qid: str, relation_pid: str
    ) -> tp.Dict[str, tp.List[Entity]]:
        try:
            return self.tail_entities[f"{head_qid}@{relation_pid}"]
        except KeyError:
            return "Not Found!"

    def get_tail_values_given_head_and_relation(
        self, head_qid: str, relation_pid: str
    ) -> tp.List[str]:
        try:
            return self.tail_values[f"{head_qid}@{relation_pid}"]
        except KeyError:
            return "Not Found!"

    def get_external_id_given_head_and_relation(
        self, head_qid: str, relation_pid: str
    ) -> tp.List[str]:
        try:
            return self.external_ids[f"{head_qid}@{relation_pid}"]
        except KeyError:
            return "Not Found!"


class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ("/RPC2",)


class XMLRPCWikidataQueryServer(WikidataQueryServer):
    def __init__(self, addr, server_args, requestHandler=RequestHandler):
        super().__init__(
            chunk_number=server_args.chunk_number, data_dir=server_args.data_dir
        )
        self.server = SimpleXMLRPCServer(addr, requestHandler=requestHandler)
        self.server.register_introspection_functions()
        self.server.register_function(self.get_all_relations_of_an_entity)
        self.server.register_function(
            self.get_tail_entities_given_head_and_relation
        )
        self.server.register_function(self.label2pid)
        self.server.register_function(self.label2qid)
        self.server.register_function(self.pid2label)
        self.server.register_function(self.qid2label)
        self.server.register_function(
            self.get_tail_values_given_head_and_relation
        )
        self.server.register_function(
            self.get_external_id_given_head_and_relation
        )
        self.server.register_function(self.mid2qid)

    def serve_forever(self):
        self.server.serve_forever()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data_dir", type=str, required=True, help="Path to the data directory"
    )
    parser.add_argument(
        "--chunk_number", type=int, required=True, help="Chunk number"
    )
    parser.add_argument("--port", type=int, default=23546, help="Port number")
    parser.add_argument("--host_ip", type=str, required=True, help="Host IP")
    args = parser.parse_args()
    print("Start with my program now!!!")
    server = XMLRPCWikidataQueryServer(
        addr=("0.0.0.0", args.port), server_args=args
    )
    with open("server_urls_new.txt", "a") as f:
        f.write(f"http://{args.host_ip}:{args.port}\n")
    print(f"XMLRPC WDQS server ready and listening on 0.0.0.0:{args.port}")
    server.serve_forever()

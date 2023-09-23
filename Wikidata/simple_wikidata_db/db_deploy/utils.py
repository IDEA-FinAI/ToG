from collections import defaultdict
from dataclasses import dataclass
from traitlets import default
import ujson as json
import os


@dataclass
class Entity:
    qid: str
    label: str


@dataclass
class Relation:
    pid: str
    label: str


def a_factory():
    return {"head": [], "tail": []}


def jsonl_generator(fname):
    """Returns generator for jsonl file."""
    for line in open(fname, "r"):
        line = line.strip()
        if len(line) < 3:
            d = {}
        elif line[len(line) - 1] == ",":
            d = json.loads(line[: len(line) - 1])
        else:
            d = json.loads(line)
        yield d


def get_batch_files(fdir):
    """Returns paths to files in fdir."""
    filenames = os.listdir(fdir)
    filenames = [os.path.join(fdir, f) for f in filenames]
    print(f"Fetched {len(filenames)} files from {fdir}")
    return filenames


# Build these 4 dictionaries
def read_entity_label(filename):
    qid_to_name = {}
    name_to_qid = defaultdict(list)
    for item in jsonl_generator(filename):
        qid_to_name[item["qid"]] = item["label"]
        name_to_qid[item["label"]].append(item["qid"])
    return qid_to_name, name_to_qid


def read_relation_label(filename):
    pid_to_name = {}
    name_to_pid = defaultdict(list)
    for item in jsonl_generator(filename):
        pid_to_name[item["pid"]] = item["label"]
        name_to_pid[item["label"]].append(item["pid"])
    return pid_to_name, name_to_pid

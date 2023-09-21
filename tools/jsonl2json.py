import json

def jsonl_to_json(jsonl_file, json_file):
    with open(jsonl_file, 'r') as infile:
        with open(json_file, 'w') as outfile:
            json_lines = infile.readlines()
            json_list = [json.loads(line) for line in json_lines]
            json.dump(json_list, outfile, indent=4)

# 用法示例
jsonl_to_json('ToG_cwq.jsonl', 'ToG_cwq.json')
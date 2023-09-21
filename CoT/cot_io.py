import json
import argparse
from tqdm import tqdm
from utils import *
from prompt_list import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str,
                        default="cwq", help="choose the dataset.")
    parser.add_argument("--prompt_methods", type=str,
                        default="cot", help="cot or io.")
    parser.add_argument("--max_length", type=int,
                        default=256, help="the max length of LLMs output.")
    parser.add_argument("--temperature", type=int,
                        default=0, help="the temperature")
    parser.add_argument("--LLM_type", type=int,
                        default="gpt-3.5-turbo", help="base LLM model.")
    parser.add_argument("--opeani_api_keys", type=int,
                        default="", help="if the LLM_type is gpt-3.5-turbo or gpt-4, you need add your own openai api keys.")
    args = parser.parse_args()

with open("cot_{}.jsonl".format(args.dataset), 'a+', encoding="UTF-8") as out:
    datas, question_string = prepare_dataset(args.dataset)
    for i in tqdm(datas, total=len(datas)):
        if args.prompt_methods == "cot":
            prompt = cot_prompt + "\n\nQ: " + i[question_string] + "\nA: "
        else:
            prompt = io_prompt + "\n\nQ: " + i[question_string] + "\nA: "
        results = run_llm(prompt, args.temperature, args.max_length, args.opeani_api_keys, args.LLM_type)
        out.write(json.dumps({"question": i[question_string], "{}_result".format(args.prompt_methods): results})+'\n')

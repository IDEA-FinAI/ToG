import json
from tqdm import tqdm
import argparse
import random
from wiki_func import *
from client import *


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str,
                        default="cwq", help="choose the dataset.")
    parser.add_argument("--max_length", type=int,
                        default=256, help="the max length of LLMs output.")
    parser.add_argument("--temperature_exploration", type=int,
                        default=0.4, help="the temperature in exploration stage.")
    parser.add_argument("--temperature_reasoning", type=int,
                        default=0.4, help="the temperature in reasoning stage.")
    parser.add_argument("--width", type=int,
                        default=3, help="choose the search width of ToG.")
    parser.add_argument("--depth", type=int,
                        default=3, help="choose the search depth of ToG.")
    parser.add_argument("--remove_unnecessary_rel", type=int,
                        default=True, help="whether removing unnecessary relations.")
    parser.add_argument("--LLM_type", type=int,
                        default="gpt-3.5-turbo", help="base LLM model.")
    parser.add_argument("--opeani_api_keys", type=int,
                        default="", help="if the LLM_type is gpt-3.5-turbo or gpt-4, you need add your own openai api keys.")
    parser.add_argument("--num_retain_entity", type=int,
                        default=5, help="Number of entities retained during entities search.")
    parser.add_argument("--addr_list", type=int,
                        default=5, help="Number of entities retained during entities search.")
    args = parser.parse_args()
        
    datas, question_string = prepare_dataset(args.dataset)

    for data in tqdm(datas):
        question = data[question_string]
        topic_entity = data['topic_entity']
        cluster_chain_of_entities = []
        pre_relations = [], 
        pre_heads= [-1] * len(topic_entity)
        flag_printed = False
        addr_list = 'ToG/ToG-E/server_urls.txt'
        with open(addr_list, "r") as f:
            server_addrs = f.readlines()
            server_addrs = [addr.strip() for addr in server_addrs]
        print(f"Server addresses: {server_addrs}")
        wiki_client = MultiServerWikidataQueryClient(server_addrs)
        for depth in range(1, args.depth+1):
            current_entity_relations_list = []
            i=0
            for entity in topic_entity:
                if entity!="[FINISH_ID]":
                    retrieve_relations_with_scores = relation_search_prune(entity, topic_entity[entity], pre_relations, pre_heads[i], question, args, wiki_client)  # best entity triplet, entitiy_id
                    current_entity_relations_list.extend(retrieve_relations_with_scores)
                i+=1
            total_candidates = []
            total_scores = []
            total_relations = []
            total_entities_id = []
            total_topic_entities = []
            total_head = []

            for entity in current_entity_relations_list:
                value_flag=False
                if entity['head']:
                    entity_candidates_id, entity_candidates_name = entity_search(entity['entity'], entity['relation'], True)
                else:
                    entity_candidates_id, entity_candidates_name = entity_search(entity['entity'], entity['relation'], False)

                if len(entity_candidates_id) ==0: # values
                    value_flag=True
                    if len(entity_candidates_name) >=20:
                        entity_candidates_name = random.sample(entity_candidates_name, 10)
                    entity_candidates_id = ["[FINISH_ID]"] * len(entity_candidates_name)
                else: # ids
                    entity_candidates_id, entity_candidates_name = del_all_unknown_entity(entity_candidates_id, entity_candidates_name)
                    if len(entity_candidates_id) >=20:
                        indices = random.sample(range(len(entity_candidates_name)), 10)
                        entity_candidates_id = [entity_candidates_id[i] for i in indices]
                        entity_candidates_name = [entity_candidates_name[i] for i in indices]

                if len(entity_candidates_id) ==0:
                    continue

                scores, entity_candidates, entity_candidates_id = entity_score(question, entity_candidates_id, entity_candidates_name, entity['score'], entity['relation'], args)
                
                total_candidates, total_scores, total_relations, total_entities_id, total_topic_entities, total_head = update_history(entity_candidates, entity, scores, entity_candidates_id, total_candidates, total_scores, total_relations, total_entities_id, total_topic_entities, total_head, value_flag)
            
            if len(total_candidates) ==0:
                half_stop(question, cluster_chain_of_entities, args)
                break
                
            flag, cluster_chain_of_entities, entities_id, pre_relations, pre_heads = entity_prune(total_entities_id, total_relations, total_candidates, total_topic_entities, total_head, total_scores, args, wiki_client)
            if flag:
                stop, results = reasoning(question, cluster_chain_of_entities, args)
                if stop:
                    print("ToG stoped at depth %d." % depth)
                    save_2_jsonl(question, results, cluster_chain_of_entities, file_name=args.dataset)
                    flag_printed = True
                else:
                    print("depth %d still not find the answer." % depth)
                    topic_entity = {entity: wiki_client.query_all("qid2label", entity) for entity in entities_id}
                    continue
            else:
                half_stop(question, cluster_chain_of_entities, args)
        
        if not flag_printed:
            results = generate_without_explored_paths(question, args)
            save_2_jsonl(question, results, [], file_name=args.dataset)

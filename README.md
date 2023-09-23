# ToG

The code for paper: "Think-on-Graph: Deep and Responsible Reasoning of Large Language Model with Knowledge Graph".


## Get started
Before running ToG, please ensure that you have successfully installed either **Freebase** or **Wikidata** on your local machine. The comprehensive installation instructions and necessary configuration details can be found in the `README.md` file located within the respective folder.

The required libraries for running ToG can be found in `requirements.txt`.

When using the Wikidata service, copy the `client.py` and `server_urls.txt` files from the `Wikidata` directory into the `ToG` folder.


# How to run
Upon successfully installing all the necessary configurations, you can proceed to execute ToG directly by employing the following command:

```sh
python main_freebase.py \  # if you wanna use Wikidata as KG source, run main_wiki.py
--dataset cwq \ # dataset your wanna test, see ToG/data/README.md
--max_length 256 \ 
--temperature_exploration 0.4 \ # the temperature in exploration stage.
--temperature_exploration 0 \ # the temperature in reasoning stage.
--width 3 \ # choose the search width of ToG, 3 is the default setting.
--depth 3 \ # choose the search depth of ToG, 3 is the default setting.
--remove_unnecessary_rel True \ # whether removing unnecessary relations.
--LLM_type gpt-3.5-turbo \ # the LLM you choose
--opeani_api_keys sk-xxxx \ # your own api keys, if LLM_type == llama, this parameter would be rendered ineffective.
--num_retain_entity 5 \ # Number of entities retained during entities search.
--prune_tools llm \ # prune tools for ToG, can be llm (same as LLM_type), bm25 or sentencebert.
```

All the pruning and reasoning prompts utilized in the experiment are in the `prompt_list.py` file.

# How to eval
Upon obtaining the result file, such as `ToG_cwq.jsonl`, you should using the `jsonl2json.py` script from the `tools` directory to convert the `ToG_cwq.jsonl` to `ToG_cwq.json`. Then, evaluate using the script in the `eval` folder (see `README.md` in `eval` folder).


# Claims
This project uses the Apache 2.0 protocol. The project assumes no legal responsibility for any of the model's output and will not be held liable for any damages that may result from the use of the resources and output.
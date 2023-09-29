# ToG

The code for paper: "Think-on-Graph: Deep and Responsible Reasoning of Large Language Model on Knowledge Graph".

## Project Structure
- `requirements.txt`: Pip environment file.
- `data/`: Evaluation datasets. See `data/README.md` for details.
- `CoT/`: CoT methods. See `CoT/README.md` for details.
- `eval/`: Evaluation script. See `eval/README.md` for details.
- `Freebase/`: Freebase environment setting. See `Freebase/README.md` for details.
- `Wikidata/`: Wikidata environment setting. See `Wikidata/README.md` for details.
- `tools/`: Common tools used in ToG. See `tools/README.md` for details.
- `ToG/`: Source codes.
  - `client.py`: Pre-defined Wikidata APIs, copy from `Wikidata/`.
  - `server_urls.txt`: Wikidata server urls, copy from `Wikidata/`.
  - `main_freebase.py`: The main file of ToG where Freebase as KG source. See `README.md` for details.
  - `main_wiki.py`: Same as above but using Wikidata as KG source. See `README.md` for details.
  - `prompt_list.py`: The prompts for the ToG to pruning, reasoning and generating.
  - `freebase_func.py`: All the functions used in `main_freebase.py`.
  - `wiki_func.py`: All the functions used in `main_wiki.py`.
  - `utils.py`: All the functions used in ToG.

## Get started
Before running ToG, please ensure that you have successfully installed either **Freebase** or **Wikidata** on your local machine. The comprehensive installation instructions and necessary configuration details can be found in the `README.md` file located within the respective folder.

The required libraries for running ToG can be found in `requirements.txt`.

When using the Wikidata service, copy the `client.py` and `server_urls.txt` files from the `Wikidata` directory into the `ToG` folder.


# How to run
See `ToG/` README.md

# How to eval
Upon obtaining the result file, such as `ToG_cwq.jsonl`, you should using the `jsonl2json.py` script from the `tools` directory to convert the `ToG_cwq.jsonl` to `ToG_cwq.json`. Then, evaluate using the script in the `eval` folder (see `README.md` in `eval` folder).


# How to cite
If you interested or inspired by this work, you can cite us by:
```sh
@misc{sun2023thinkongraph,
      title={Think-on-Graph: Deep and Responsible Reasoning of Large Language Model with Knowledge Graph}, 
      author={Jiashuo Sun and Chengjin Xu and Lumingyuan Tang and Saizhuo Wang and Chen Lin and Yeyun Gong and Heung-Yeung Shum and Jian Guo},
      year={2023},
      eprint={2307.07697},
      archivePrefix={arXiv},
      primaryClass={cs.CL}
}
```
# Claims
This project uses the Apache 2.0 protocol. The project assumes no legal responsibility for any of the model's output and will not be held liable for any damages that may result from the use of the resources and output.
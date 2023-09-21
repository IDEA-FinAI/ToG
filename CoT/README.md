# CoT

In this folder are the experiments that correspond to the CoT and IO prompt in the main experiment table.

Make sure you have installed all the requirements:
```sh
tqdm
openai
```
>
If you want to use a non-openai model like LLAMA, make sure to download [vllm](https://github.com/vllm-project/vllm) and turn on the api service with the following command:

```sh
python -m vllm.entrypoints.openai.api_server \
--model meta-llama/Llama-2-70b-chat-hf \
--tensor-parallel-size 8 \
--max-num-batched-tokens 4096
```

For the `Llama-2-70b-chat-hf`, it is recommended to running with 8 A100-40Gs.

### How to run
If you have already configured all the requirements, you can just execute the following command:
```sh
python cot_io.py \
--dataset cwq \ # dataset your wanna test, see ToG/data/README.md
--prompt_methods cot \ # cot or io prompt
--max_length 256 \ 
--temperature 0 \ # We recommend the temperature setting of 0 for reproducible results.
--LLM_type gpt-3.5-turbo \ # the LLM you choose
--opeani_api_keys sk-xxxx \ # your own api keys, if LLM_type == llama, this parameter would be rendered ineffective.
```

### How to eval
After finish ToG and generating the result file (such as `CoT_cwq.jsonl`), proceed to the "eval" directory `README.md`.
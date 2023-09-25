# Eval

We use **Exact Match** as our evaluation metric.

After getting the final result file, use the following command to evaluate the results:

```sh
python eval.py \  # if you wanna use Wikidata as KG source, run main_wiki.py
--dataset cwq \ # dataset your wanna test, see ToG/data/README.md
--output_file ToG_cwq.json \ 
--constraints_refuse True
```

After that, you will get a result json file that contains:

```sh
{
    'dataset': 
    'method': 
    'Exact Match': 
    'Right Samples': 
    'Error Sampels': 
}
```
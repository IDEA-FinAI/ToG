# simple-wikidata-db

This library provides a set of scripts to download the Wikidata dump, sort it into staging files, and query the data in these staged files in a distributed manner. The staging is optimized for (1) querying time, and (2) simplicity.

This library is helpful if you'd like to issue queries like:

- Fetch all QIDs which are related to [Q38257](https://www.wikidata.org/wiki/Q38257)
- Fetch all triples corresponding to the relation (e.g. [P35](https://www.wikidata.org/wiki/Property:P35))
- Fetch all aliases for a QID

## Downloading the dump

A full list of available dumps is available [here](https://dumps.wikimedia.org/wikidatawiki/entities/). To fetch the most recent dump, run:

```
wget https://dumps.wikimedia.org/wikidatawiki/entities/latest-all.json.gz
```

or, if aria2c is installed, run:

```
aria2c --max-connection-per-server 16 https://dumps.wikimedia.org/wikidatawiki/entities/latest-all.json.gz
```

Downloading takes about 2-5 hours (depending on bandwidth).

## Processing the dump

The original downloaded wikidata dump is a single file and combines different types of information (alias names, properties, relations, etc). We preprocess the dump by iterating over the compressed file, and saving information to different subdirectories. For more information, see the [Data Format](#data-format). To preprocess the dump, run:

```bash
python3 preprocess_dump.py \ 
    --input_file $PATH_TO_COMPRESSED_WIKI_JSON \
    --out_dir $DIR_TO_SAVE_DATA_TO \
    --batch_size $BATCH_SIZE \
    --language_id $LANG
```

These arguments are:

- `input_file`: path to the compressed JSON Wikidata dump json file
- `out_dir`: path to directory where tables will be written. Subdirectories will be created under this directory for each table.
- 'num_lines_read': number of lines to read. Useful for debuggin.
- `num_lines_in_dump`: specifies the total number of lines in the uncompressed json file. This is used by a tqdm bar to track progress. As of January 2022, there are 95,980,335 lines in latest-all.json. It takes about ~21 minutes to run `wc -l latest-all.json`.
- `batch_size`: The number of triples to write into each batch file that is saved under a table directory.
- `language_id`: The language to use when extracting entity labels, aliases, descriptions, and wikipedia links

Additionally, running with the flag `--test` will terminate after processing an initial chunk, allowing you to verify results.

It takes ~5 hours to process the dump when running with 90 processes on a 1024GB machine with 56 cores. A tqdm progress bar should provide a more accurate estimate while data is being processed.  

## Data Format

The Wikidata dump is made available as a single, unweildy JSON file. To make querying/filtering easier, we split the information contained in this JSON file into multiple **tables**, where each table contains a certain type of information. The tables we create are described below:

| Table name    | Table description   | Table schema|
| --------------- |:--------------------| :-----|
| labels          | Holds the labels for different entities | qid: the QID of the entity <br> label: the entity's label ('name') |
| descriptions    | Holds the descriptions for different entities | qid: the QID of the entity <br> description: the entity's description (short summary at the top of the page) |
| aliases         | Holds the aliases for different entities  | qid: the QID of the entity <br> alias: an alias for the entity |
| entity_rels     | Holds statements where the value of the statement is another wikidata entity | claim_id: the ID for the statement <br> qid: the ID for wikidata entity <br> property_id: the ID for the property <br> value: the qid for the value wikidata entity |
| external_ids    | Holds statements where the value of the statement is an identifier to an external database (e.g. Musicbrainz, Freebase, etc) | claim_id: the ID for the statement <br> qid: the ID for wikidata entity <br> property_id: the ID for the property <br> value: the identifier for the external ID |
| entity_values   | Holds statements where the value of the statement is a string/quantity | claim_id: the ID for the statement <br> qid: the ID for wikidata entity <br> property_id: the ID for the property <br> value: the value for this property |
| qualifiers      | Holds qualifiers for statements |  qualifier_id: the ID for the qualifier <br> claim_id: the ID for the claim being qualified <br> property_id: the ID for the property <br> value: the value of the qualifier |
| wikipedia_links | Holds links to Wikipedia items | qid: the QID of the entity <br> wiki_title: link to corresponding wikipedia entity  |
| plabels | Holds PIDs and their corresponding labels | pid: the PID of the property <br> label: the label for the property |
----

<br><br>
Each table is stored in a directory, where the content of the table is written to multiple jsonl files stored inside the directory (each file contains a subset of the rows in the table). Each line in the file corresponds to a different triple. Partitioning the table's contents into multiple files improves querying speed--we can process each file in parallel.

## Querying scripts

Two scripts are provided as examples of how to write parallelized queries over the data once it's been preprocessed:

- `fatching/fetch_with_name.py`: fetches all QIDs which are associated with a particular name. For example: all entities associated with the name 'Victoria', which would inclue entities like Victoria Beckham, or Victoria (Australia).
- `fatching/fetch_with_rel_and_value.py`: fetches all QIDs which have a relationship with a specific value. For example: all triples where the relation is P413 and the object of the relation is Q622747.

# Instructions for deploying a query service locally

## Making index

Use `simple_wikidata_db/db_deploy/build_index` to build a dict index for in-memory fast query:

```bash
python simple_wikidata_db/db_deploy/build_index.py \
    --input_dir $PREPROCESS_DATA_DIR \
    --output_dir $INDEX_FILE_DIR \
    --num_chunks $NUM_CHUNKS \
    --num_workers $NUM_WORKERS \
    --chunk_idx $CHUNK_IDX
```

- `input_dir`: The preprocessed wikidata dump dir. It should be the output dir of the preprocessing job described above.
- `output_dir`: The dir where the generated index is stored. it is usually a subfolder of `input_dir`, in this case it is `input_dir`/indices
- `num_chunks`: The number of chunks to split the data into. This is used to split the data into multiple files, which can be queried in parallel.
- `num_workers`: number of subprocesses in this job.
- `chunk_idx`: Which chunk of the whole index to build. By default it's -1, where all chunks are built sequentially. If you want to build a specific chunk, set it to the index of the chunk.

Note that index is deeply coupled with query interfaces. So if you have any new requirements for querying the data, you may need to modify the index building script `build_index.py` by yourself. Construction of index chunks can be parallized or distributed.

Please also note that index building is a memory-intensive task. A chunk of 1/10 the total size of the data requires ~200GB of memory. So you may need to adjust the chunk size according to your machine's memory. For a 1/10 chunk index, its construction takes ~30mins for worker=400.

## Deploying the database

Use `simple_wikidata_db/db_deploy/server` to start a server with a chunk of data and listening on a port:

```bash
python simple_wikidata_db/db_deploy/server.py \
    --data_dir $INDEX_FILE_DIR \
    --chunk_number $CHUNK_NUMBER
```

- `data_dir`: The dir of the processed data. Its `indices` subfolder should contain the index files. Usually this should be the same as `input_dir` in the index building step.
- `chunk_number`: The chunk number of the data to be served. This should be the same as the `chunk_idx` in the index building step. A single process can only serve one chunk of data. If you want to serve multiple chunks, you need to start multiple processes.

The service is implemented via XML-RPC. A server process will listen on port 23546 (this is hardcoded in `server.py`). And clients can connect to the server via `http://[server_ip]:23546`. All queries are implemented via python's builtin support for `xmlrpc`, and code is written with the help of ChatGPT.

Similar to index construction, this service is deployed in a distributed manner. Specifically, each server process reads 1 chunk of data, which takes ~200GB of memory for a chunk of 1/10 the total size. So you may need to adjust the chunk size according to your machine's memory. Reading index is also very time-consuming. For a 1/10 chunk index, it takes ~20mins to load the index into memory.

## Querying the database

An example client is provided in `db_deploy/client.py`. It can be used to query the database:

```bash
python simple_wikidata_db/db_deploy/client.py --addr_list server_urls.txt
```

For a single query, the client sends the query to all server nodes, get results, and aggregate locally.

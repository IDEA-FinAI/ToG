#!/bin/bash

rm server_urls.txt

for i in {0..9}; do
    python -u simple_wikidata_db/db_deploy/server.py --data_dir /dev/shm/wikidump_inmem/wikidump_20230116 --chunk_number $i --port 2315$i > logs/server_log_$i.log 2>&1 &
done

wait

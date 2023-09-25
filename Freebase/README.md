# Freebase Setup

## Requirements

- OpenLink Virtuoso 7.2.5 (download from this [link](https://sourceforge.net/projects/virtuoso/files/virtuoso/))
- Python 3
- Freebase dump from this [link](https://developers.google.com/freebase?hl=en)

## Setup

### Data Preprocessing

We use this py script ([link)](https://github.com/lanyunshi/Multi-hopComplexKBQA/blob/master/code/FreebaseTool/FilterEnglishTriplets.py), to clean the data and remove non-English or non-digital triplets:

```shell
gunzip -c freebase-rdf-latest.gz > freebase # data size: 400G
nohup python -u FilterEnglishTriplets.py 0<freebase 1>FilterFreebase 2>log_err & # data size: 125G
```

## Import data

we import the cleaned data to virtuoso, 

```shell
tar xvpfz virtuoso-opensource.x86_64-generic_glibc25-linux-gnu.tar.gz
cd virtuoso-opensource/database/
mv virtuoso.ini.sample virtuoso.ini

# ../bin/virtuoso-t -df # start the service in the shell
../bin/virtuoso-t  # start the service in the backend.
../bin/isql 1111 dba dba # run the database

# 1、unzip the data and use rdf_loader to import
SQL>
ld_dir('.', 'FilterFreebase', 'http://freebase.com'); 
rdf_loader_run(); 
```

Wait for a long time and then ready to use.

## Mapping data to Wikidata

Due to the partial incompleteness of the data present in the freebase dump, we need to map some of the entities with missing partial relationships to wikidata. We download these rdf data via this [link](https://developers.google.com/freebase?hl=en#freebase-wikidata-mappings)

we can use the above method to add it into virtuoso.

## Test example

```python
import json
from SPARQLWrapper import SPARQLWrapper, JSON

SPARQLPATH = "http://localhost:8890/sparql"

def test():
    try:
        sparql = SPARQLWrapper(SPARQLPATH)
        sparql_txt = """PREFIX ns: <http://rdf.freebase.com/ns/>
            SELECT distinct ?name3
            WHERE {
            ns:m.0k2kfpc ns:award.award_nominated_work.award_nominations ?e1.
            ?e1 ns:award.award_nomination.award_nominee ns:m.02pbp9.
            ns:m.02pbp9 ns:people.person.spouse_s ?e2.
            ?e2 ns:people.marriage.spouse ?e3.
            ?e2 ns:people.marriage.from ?e4.
            ?e3 ns:type.object.name ?name3
            MINUS{?e2 ns:type.object.name ?name2}
            }
        """
        #print(sparql_txt)
        sparql.setQuery(sparql_txt)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        print(results)
    except:
        print('Your database is not installed properly !!!')

test()

```

## 

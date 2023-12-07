# Datasets

The current folder holds all the datasets we used, the statistics of the datasets used in the paper are shown in table below:

| Dataset             | Answer Format | Train     | Test  | Licence     | Mid (For Freebase) | Qid (For Wikidata) |
| ------------------- | ------------- | --------- | ----- | ----------- | ------------------ | ------------------ |
| ComplexWebQuestions | Entity        | 27,734    | 3,531 | -           | √                  | √                  |
| WebQSP              | Number        | 3,098     | 1,639 | CC License  | √                  | √                  |
| GrailQA*            | Entity/Number | 44,337    | 1,000 | -           | √                  |                    |
| QALD-10             | Entity/Number | -         | 333   | MIT License |                    | √                  |
| Simple Question*    | Number        | 14,894    | 1,000 | CC License  | √                  |                    |
| WebQuestions        | Entity/Number | 3,778     | 2,032 | -           | √                  | √                  |
| T-REx               | Entity        | 2,284,168 | 5,000 | MIT License |                    | √                  |
| Zero-Shot RE        | Entity        | 147,909   | 3,724 | MIT License |                    | √                  |
| Creak               | Bool          | 10,176    | 1,371 | MIT License |                    | √                  |

where * denotes we randomly selected 1,000 samples from the GrailQA and Simple Questions test set to constitute the testing set owing to the abundance of test samples.

If the user wants to search with a different KG source, check out the `mid2qid` and `qid2mid` APIs of the simple-wikidata-db folder. We have put the mid and qid used in our experiments into the dataset.

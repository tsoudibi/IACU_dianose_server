# IACU_dianose_server 


# Installation
`git clone https://github.com/tsoudibi/IACU_dianose_server.git` 

## requrement
`pip install requirements.txt`

## run server
```
cd .\server\
python .\main.py
```
the server is successfully starting when seeing
```
starting server...
starting server...
+---------------------------------------------------------------------+
  Welcome to MONPA: Multi-Objective NER POS Annotator for Chinese
+---------------------------------------------------------------------+
已找到 model檔。Found model file.
load users DB successful!
reading database file...
done!
loading embedder...
done!
 * Serving Flask app 'main' (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
06/12/2022 00:28:06 - INFO - werkzeug -  * Running on all addresses (0.0.0.0)
   WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://127.0.0.1:3001
 * Running on http://192.168.0.25:3001 (Press CTRL+C to quit)
```
First time of strating server might take longer time, cause it need to download BERT model.

-----------------------
# File discription
in `server` ...

## `main.py` 
Contain the Flask framwork server.<br>
Handeling request from others.

## `Medical_Bot.py`
The main part of dianosis, implement in following steps:
1. First, when recieving user's resquest, check the `UID` and load checkpoint (if exist).
2. Then, use $MONPA$ to implememt "word segmentation" and "POS tagging".
3. Use $BERT$ to filter out words that is not a symptoms.
4. Pass through the database(`disease_to_acu_and_symptom_modify_ZH_faceonly_embedding.csv`) and found the candidate diseases corresponding of those symptoms.
5. Use basic decision tree to generate response.
6. Response to user

## `user_DB.py`
Save or update checkpoints of all user in `users_log.json` whenever recieving a request.<br>
Users are identified by `UID`, which is given by APP.<br>
The purpose of saving and loading checkpoint is to handel muti-user requests at the same time. 

## `disease_to_acu_and_symptom_modify_ZH_faceonly_embedding.csv`
The main database with following columns:
| disease_ID | disease_name | ICD9 | meridian | symptoms_origin | symptoms | acupoints | symptoms_embeddings |
| ----       | ----         | ---- | ----     | ----            | ----     | ----      | ----                |
| DIS0155    | 眼球震顫    | 379.5| 足太陽膀胱經 | ['眼球震顫'] | ['眼球震顫'] | "['睛明', '球後']" | $SKIP$ |

## `MONPA_dictionary.txt`
The dictionary containing the word we don't want MONPA to segment.

## `users_log.json`
The database containing checkpoints of all users.<br>
Feel free to delete it, server will re-construct one when it can't find this file.

-----------------------
# Usage
## /init/
* for every dianose, `/init/` request should be done before `/ask/`.
* request METHOD: POST
* request content type: Form
request formate:
```
{
    "uid":0,
    "user_name":"testuser"
}
```
* response content type: JSON
response formate:
```
{
    "uid":0,
    "question":"hello"
}
```

## /ask/
* for every dianose, `/init/` request should be done before `/ask/`.
* request METHOD: POST
* request content type: Form
request formate:
```
{
    "uid":0,
    "answer":"I have hadache"
}
```
* response content type: JSON
response formate:
```
{
    "uid":0,
    "response":"I am a string", 
    "acu_points":[
        "acu1",
        "acu2"
    ], 
    "continue": True
}
```
-----------------------
# Data creation
## `disease_to_acu_and_symptom_modify_ZH_faceonly_embedding.csv`
used data files: 
 - `data-O.xlsx`
 - `disease.xlsx`
 - `disease_target.json`

used processing files:
 - `Merge_excel.py`
 - `disease_to_acu_and_symptom.ipynb`
 - `Data_Preprocessing.ipynb`

<br><br>
steps of generating data:
1. Use `Merge_excel.py` to merge data from `data-O.xlsx` and `disease.xlsx`, generating `Merge_excel.xlsx`
2. Use `disease_to_acu_and_symptom.ipynb` to drop unused column, null value and duplicate value, generating `disease_to_acu_and_symptom.csv`
3. Translate to ZH, `disease_to_acu_and_symptom_ZH.csv`
4. Use `Data_Preprocessing.ipynb`,and...
    1. by `disease_target.json`, filtering acupoints to face-only acupoints
    2. drop the disease that has no symptoms
    3. useing $BERT$ embedding model, generate enbedding for each disease's symptoms
    4. finally, save result as `disease_to_acu_and_symptom_modify_ZH_faceonly_embedding.csv`
<br>
save pre-caculated embedding in csv can help reduce the time when comparing user input and database 

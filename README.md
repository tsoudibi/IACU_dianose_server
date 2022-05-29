# IACU_dianose_server 


# Installation
`git clone https://github.com/tsoudibi/IACU_dianose_server.git` 

## requrement
`pip install requirements.txt`


-----------------------
# Usage
## /init/
* for every dianose, `/init/` request should be done first.
* request METHOD: POST
* request content type: JSON
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
    "UID":0,
    "question":"hello"
}
```

## /ask/
* request METHOD: POST
* request content type: JSON
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
    "UID":0,
    "response":"I am a string", 
    "acu_points":[
        "acu1",
        "acu2"
    ], 
    "continue": True
}
```

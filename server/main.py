#-*- encoding: UTF-8 -*-
print('starting server...')
import re
from flask import Flask, request
from flask import jsonify

from Medical_Bot import Medical_Bot
from users_DB import USERS_DB


# get sentence from web in json format
# -------------------------------------------
# flask partition
app = Flask(__name__)

# enable medical bot
UDB = USERS_DB()
MB = Medical_Bot(UDB)

# return question + uid
@app.route('/init/', methods=['POST'])
def post():
    # quest = request.json
    UID = request.form["uid"]
    USER_NAME = request.form["user_name"]

    # check if this user is new and add to users DB
    UDB.new_user(UID,USER_NAME)

    # clear checkpoints
    MB.reset_inquiry()
    UDB.reset_checkpoint(UID)

    key = ["uid", "question"]
    value = [UID, "哈囉" + USER_NAME + "，你有什麼症狀呢？"]
    dic = dict(zip(key, value))

    # save response in JSON
    UDB.save_response(UID, dic['question'])
    print(dic, jsonify(dic))
    return jsonify(dic)


# return uid + question + target["id"] + continue
@app.route('/ask/', methods=['POST'])
def post2():
    # quest = request.json
    UID = request.form['uid']

    # save answer in JSON
    # print(request.form["answer"])
    UDB.save_answer(UID, request.form["answer"])
    
    
    # if cont = true:
        # 繼續問診
    # else
        # if disease == [] 
            # means query faild, restart
        # else if disease = ["EX-HN3"] 
            # means find this acu point
            
    # do the inquiry
    response,cont = MB.inquiry(UID, request.form["answer"])
    print(response)

    # save response in JSON
    UDB.save_response(UID, response)
    
    # uid, question, target[id], continue
    key = ["uid", "response", "acu_points", "continue"]
    value = [UID, response, MB.target_acupoint, cont]
    dic = dict(zip(key, value))
    print(dic)
    return jsonify(dic)

@app.route('/', methods=['POST'])
def no():
    print('no')
    return 'nonononon'

@app.route('/test/', methods=['POST'])
def no22():
    quest = request.json
    print(quest)
    return quest
# -------------------------------------------

if __name__ == '__main__':
    app.config['JSON_AS_ASCII'] = False
    app.run(host='0.0.0.0',port=3001)


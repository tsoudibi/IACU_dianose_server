#-*- encoding: UTF-8 -*-
print('starting server...')
from flask import Flask, request
from flask import jsonify

from Medical_Bot import Medical_Bot


# get sentence from web in json format
# -------------------------------------------
# flask partition
app = Flask(__name__)

# enable medical bot
MB = Medical_Bot()

# return question + uid
@app.route('/init/', methods=['POST'])
def post():
    quest = request.json
    MB.reset_inquiry()
    key = ["uid", "question"]
	# value = [uid, "你好%s,請問你哪裡不舒服呢？" % (name['name'])]
    value = [000, "哈摟，你有甚麼症狀呢？"]
    dic = dict(zip(key, value))
    return jsonify(dic)


# return uid + question + target["id"] + continue
@app.route('/ask/', methods=['POST'])
def post2():
    quest = request.json
    print(quest)
    
    
    # if cont = true:
        # 繼續問診
    # else
        # if disease == [] 
            # means query faild, restart
        # else if disease = ["EX-HN3"] 
            # means find this acu point
            
    response,cont = MB.inquiry(quest['answer'])
    print(response)
    
    # uid, question, target[id], continue
    key = ["uid", "question", "acu_points", "continue"]
    value = [12,response, MB.symptoms, cont]
    dic = dict(zip(key, value))
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


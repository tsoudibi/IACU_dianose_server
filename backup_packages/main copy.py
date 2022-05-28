#-*- encoding: UTF-8 -*-
import json
import socket
from zhon.hanzi import punctuation as p
from flask import Flask, request
import random
import pymysql.cursors
from flask import jsonify

# ckip address
target_host = "140.116.245.151"
target_port = 9998

# Connect to the database
connection = pymysql.connect(host='db',
                             port=3306,
                             user='root',
                             password='HvPUndB0T4BliStoGCpBFfP0MUAVrUQ3',
                             db='iacu_chatbot',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

# Ckip word parsing
def seg(sentence):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((target_host, target_port))

    data = "seg@@" + sentence
    client.send(data.encode("utf-8"))
    print("connected successfully!")

    data = bytes()
    while True:
        request = client.recv(8)
        if request:
            data += request
        else:
            break

    WSResult = []
    response = data
    if response is not None or response != '':
        response = response.decode('utf-8').split()
        for resp in response:
            resp = resp.strip()
            resp = resp[0:len(resp) - 1]
            temp = resp.split('(')
            word = temp[0]
            pos = temp[1]
            WSResult.append((word, pos))

    return WSResult


# input sentence “你好，我覺得前額有點痛，有點睡不著。”get a list s = ['你', ('好'), '我', '覺得', '前額('有點')痛', ('有點')'睡不著']
def ckip_parser(sentence):
    sents_list = []
    sents_list.append(sentence)
    stop_word = []
    with open("stop_word.txt", 'r', encoding="utf-8") as f:
        for lines in f:
            if u'\ufeff' in lines:
                lines = lines.replace(u'\ufeff', '')
            stop_word.append(lines)

    for b in range(len(sents_list)):
        sent = seg(sents_list[b])
        # print(sent)
        s = []
        for c in range(len(sent)):
            if sent[c][0] not in p:
                sen = sent[c][0] + '\n'
                if sen not in stop_word:
                    s.append(sent[c][0])
    print("Finished Ckip parsing!")
    return s


# nlp and retrieval-based chat-bot
class Medical_bot(object):

    def __init__(self, uid):
        self.uid = uid

    # s = ['你', ('好'), '我', '覺得', '前額('有點')痛', '眼花'] --> ['前額痛', '眩暈']
    # s = ['你', ('好'), '我', '覺得', '頭('有點')痛] --> ['你的前額會痛嗎？'...]
    def predict_symptom(self, sentence):
        candidate_symptom = []
        candidate_query = []
        symptom_path = "symptom_disease.json"
        with open(symptom_path, 'r', encoding='utf-8') as sym:
            symptom = json.load(sym)
            for i in range(len(symptom)):
                if symptom[i]["children"] == []:
                    for j in sentence:
                        if j in symptom[i]["concepts"]:
                            candidate_symptom.append(symptom[i]["domain"])
                else:
                    for k in sentence:
                        if k in symptom[i]["concepts"]:
                            for l in symptom[i]["children"]:
                                for t in symptom:
                                    if t["domain"] == l:
                                        candidate_query.append(t["response"])
                            candidate_symptom.append(symptom[i]["domain"])
        # print(candidate_symptom)
        return candidate_symptom, candidate_query

    # ['前額痛', '眩暈'] -> ['EX-HN3(印堂)' ...]
    def predict_disease(self, symptom):
        candidate_disease = []
        disease_path = "disease_target.json"
        with open(disease_path, 'r', encoding='utf-8') as dis:
            disease = json.load(dis)
            for i in range(len(disease["data"])):
                lent = 0
                for j in symptom:
                    if j in disease["data"][i]["attributes"]["symptom"]:
                        lent += 1
                    if lent == len(symptom):
                        candidate_disease.append(disease["data"][i]["id"])
        # print(candidate_disease)
        return candidate_disease

    # ['EX-HN3(印堂)'...] + ['前額痛', '眩暈']-> query
    # if len(target) > 20 : ask a general query
    # else : choose one target and get a new disease to ask
    def query_predict(self, symptom, disease, attention, candidate):
        query = []
        candidate_query = []
        target_disease = None
        cont = False
        if len(disease) >= 20 and not attention:
            query.append("請問你還有什麼其他症狀嗎？")
            cont = True
        elif (len(disease) < 20 and len(disease) > 1):
            target_path = "disease_target.json"
            with open(target_path, 'r', encoding='utf-8') as tar:
                target = json.load(tar)
                for i in disease:
                    for j in target["data"]:
                        if j["id"] == i:
                            for k in j["attributes"]["symptom"]:
                                target_symptom_path = "symptom_disease.json"
                                if (k not in symptom) and (k not in candidate):
                                    with open(target_symptom_path, 'r', encoding='utf-8') as tar_sym:
                                        target_symptom = json.load(tar_sym)
                                        for l in target_symptom:
                                            if l["domain"] == k:
                                                if l["response"] not in candidate_query:
                                                    candidate_query.append(l["response"])
                                        # print(candidate_query)
                                        target_query = random.choice(candidate_query)
                                        query.append(target_query)
                                        if attention:
                                            for t in target_symptom:
                                                if t["response"] == target_query:
                                                    target_disease = t["domain"]
            cont = True
        else:
            target_query = None
            cont = False
        # print(target_query)
        return target_query, target_disease, cont

# get sentence from web in json format
# -------------------------------------------
# flask partition
app = Flask(__name__)

# return question + uid
@app.route('/init', methods=['POST'])
def post():
    # name = request.json
    with connection.cursor() as cursor:
        sql = 'INSERT INTO user (NAME) VALUES ("")'
        cursor.execute(sql)
        # sql = 'INSERT INTO user (name) VALUES (%s)'
        # cursor.execute(sql, (name["name"]))
        query = 'SELECT uid, symptom FROM user ORDER BY uid DESC LIMIT 1'
        cursor.execute(query)
        rows = cursor.fetchall()
        uid = rows[0]["uid"]
    connection.commit()
    key = ["uid", "question"]
	# value = [uid, "你好%s,請問你哪裡不舒服呢？" % (name['name'])]
    value = [uid, "你好,請問你哪裡不舒服呢？"]
    dic = dict(zip(key, value))
    return jsonify(dic)

# return uid + question + target["id"] + continue
@app.route('/ask', methods=['POST'])
def post2():
    quest = request.json
    uid = quest["uid"]
    answer = quest["answer"]
    ask = True
    try:
        with connection.cursor() as cursor:
            query = 'SELECT symptom, candidate, query, ask FROM user WHERE uid = %s'
            cursor.execute(query, uid)
            rows = cursor.fetchall()
            if rows[0]["symptom"] == None:
                symptom = []
            else:
                symptom = rows[0]["symptom"].split(",")
            if rows[0]["candidate"] == None:
                candidate = []
            else:
                candidate = rows[0]["candidate"].split(",")
            if rows[0]["query"] == None:
                que = []
            else:
                que = rows[0]["query"].split(",")
            s = ckip_parser(answer)
            model = Medical_bot(uid)
            noarray = ["不知道", "沒有", "沒", "不清楚", "不會", "沒感覺", "沒覺得", "不懂", "不太清楚"]
            array = ["會", "是", "有时会", "偶尔会", "有时候会"]
            stop = ["不", "沒", "否"]
            for list1 in array:
                for list2 in stop:
                    if list1 in answer and list2 not in answer:
                        ask = False
                        break
            for lis in noarray:
                if lis in answer:
                    attention = True
                    ask = True
            if ask == False:
                cursor.execute("SELECT ask FROM user WHERE uid = %s", uid)
                row = cursor.fetchall()
                temporary = row[0]["ask"]
                with open("symptom_disease.json", 'r', encoding='utf-8') as f:
                    tem_dis = json.load(f)
                    for i in tem_dis:
                        c = ",".join(str(e) for e in i["response"])
                        if temporary in c:
                            # s.append(i["domain"])
                            symptom.append(i["domain"])
                            print("yes", ask, symptom)
                            sm = ",".join(str(e) for e in symptom)
                            cursor.execute('UPDATE user SET symptom = %s WHERE uid = %s', (sm, uid))
                cursor.execute('UPDATE user SET query = %s, ask = %s WHERE uid = %s', ('', '', uid))
            symptom2, ques = model.predict_symptom(s)
            for sy in symptom2:
                if sy not in symptom:
                    symptom.append(sy)
            sql2 = 'UPDATE user SET symptom = %s WHERE uid = %s'
            symptom1 = ",".join(str(e) for e in symptom)
            cursor.execute(sql2, (symptom1, uid))
            attention = False
            disease = model.predict_disease(symptom)
            query, target, cont = model.query_predict(symptom, disease, attention, candidate)
            candi_que = ",".join(str(e) for e in que)
            sql4 = 'UPDATE user SET query = %s, ask = %s WHERE uid = %s'
            print(query)
            if query is not None or query == "" or query == []:
                sql5 = 'UPDATE user SET ask = %s WHERE uid = %s'
                cursor.execute(sql5, (query[0], uid))
            if candi_que == "" and ques != []:
                cont = True
                query = ques[0]
                q = ",".join(str(e) for e in query)
                if type(q) is list:
                    q = q[0]
                del ques[0]
                ques1 = ",".join(str(e) for e in ques)
                cursor.execute(sql4, (ques1, q, uid))
                ask = True
            if candi_que != "" and ask:
                cont = True
                query = que[0]
                while "[" in query:
                    query = query.split("'")[1].split("'")[0]
                del que[0]
                que1 = ",".join(str(e) for e in que)
                cursor.execute(sql4, (que1, query, uid))
            if target != None:
                candidate.extend(target)
                candidate1 = ",".join(str(e) for e in candidate)
                sql3 = 'UPDATE user SET candidate = %s WHERE uid = %s'
                cursor.execute(sql3, (candidate1, uid))
        connection.commit()
    finally:
        # uid, question, target[id], continue
        if query != "" and query != [] and type(query) is list:
            query = query[0]
        key = ["uid", "question", "acu_points", "continue"]
        value = [uid, query, disease, cont]
        dic = dict(zip(key, value))
    return jsonify(dic)
# -------------------------------------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=False)


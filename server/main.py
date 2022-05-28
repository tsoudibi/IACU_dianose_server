#-*- encoding: UTF-8 -*-
print('starting server...')
import json
from urllib import response
from flask import Flask, request
import random
from flask import jsonify
from pyparsing import NoMatch

# to use the service, server need to 'pip install -U sentence-transformers '
from sentence_transformers import SentenceTransformer
import scipy.spatial
from tqdm import tqdm
import ast
import pandas as pd
import numpy as np
import itertools
import monpa
patterns=['Na','Nb','Nc','Ncd',
          'NO',
          'VA','VAC','VB','VC','VD','VE','VF','VG','VH','VHC','VI','VJ','VL']

n_patterns=['Na','Nb','Nc','Ncd']
d_patterns=['NO']
v_patterns=['VA','VAC','VB','VC','VD','VE','VF','VG','VH','VHC','VI','VJ','VL']

# medical bot
class Medical_Bot():
        
    def read_embedding_CSV(self):
        try:
            df = pd.read_csv(self.DB_file_name)
            df['symptoms'] = df['symptoms'].apply(lambda x: ast.literal_eval(x))
            df['acupoints'] = df['acupoints'].apply(lambda x: ast.literal_eval(x))
            df['symptoms_embeddings'] = df['symptoms_embeddings'].apply(lambda x: ast.literal_eval(x))
            # print(type(df.loc[0,'symptoms']), type(df.loc[0,'acupoints']),type(df.loc[0,'symptoms_embeddings']),type(df.loc[0,'symptoms_embeddings'][0]))
            # print(df.head(5))
            
            # save database as dataFrame
            self.DataBase = df
            return 
        except:
            print('error when read_embedding_CSV')

    # input: queried symptoms
    # output: 3 most possible disease
    def query_disease(self, queries):
        # encode quries
        print(len(queries))
        query_embeddings = self.embedder.encode(queries)
        
        
        # create empty disease dictionary
        score_dist = {} 
        for index, row in self.DataBase.iterrows():
            score_dist[row['disease_name']] = 0 # use dictionary to store disease name and score

        for query, query_embedding in zip(queries, query_embeddings):
            for index, row in self.DataBase.iterrows():
                dists = scipy.spatial.distance.cdist([query_embedding], self.DataBase.loc[index,'symptoms_embeddings'], "cosine")[0]

                final_dist = 0
                avaliable_count = 0
                for dist in dists:
                    if 1-dist >= self.query_threshold :
                        final_dist += dist
                        avaliable_count += 1
                # take mean value of all diatence as score_dist
                try:
                    score_dist[row['disease_name']] = score_dist[row['disease_name']] + (1-(final_dist / avaliable_count)) * (((42-len(dists))/42)*0.2 +1)
                    # score_dist[row['disease_name']] = score_dist[row['disease_name']] + (1-(final_dist / avaliable_count)) 
                    # score_dist.append(final_dist / avaliable_count)
                except:
                    score_dist[row['disease_name']] = score_dist[row['disease_name']] + 0

            # sort by distence
            results = sorted(score_dist.items(), key=lambda x:x[1], reverse=True)
        print("======================")
        print("Query:", queries)
        for name, distance in results[0:3]:
            print(name, "(Score: %.4f)" % (distance))
        
        # returning top 3 high result
        return results[0:self.query_return_number]
    
    # input: user input
    # output: response string, continue
    def inquiry(self, input_symptoms_origin):
        input_symptoms = self.MONPA_filter(input_symptoms_origin)
        # check stop word
        for stop_word in ["不", "沒", "否"]:
            if stop_word in input_symptoms_origin:
                # if there are candidate
                if len(self.candidate_dis) > 0:
                    response = '好的，你看起來像有'+self.candidate_dis[0][0]+'\n分數為'+str(round(self.candidate_dis[0][1],3))+'/'+str(len(self.symptoms))
                    return response, False
                else:
                    response = '好的，你真健康'
                    return response, False
            
        if input_symptoms in self.symptoms:
            # the symptoms has told before
            response = '你有跟我提到過這個症狀了喔\n你還有其他症狀嗎？'
            return response, True
        else:
            # put the input_symptoms into symptoms list
            self.symptoms = self.symptoms + input_symptoms
            # query_disease
            self.candidate_dis = self.query_disease(self.symptoms)
            
            if self.candidate_dis[0][1] <= 0:
                # if there are no disease found
                response = '完全找不到對應的疾病喔'
                # clear acupoints list
                self.acupoints.clear()
                return response, False
            elif self.candidate_dis[0][1] <= len(self.symptoms) -2 :
                # last input symptom useless
                response = '資料庫中沒有完全符合這些特徵的疾病。\n不過目前你看起來最像得了'+self.candidate_dis[0][0]
                return response, True
            else:
                # disease found
                # response = '你看起來像有'+self.candidate_dis[0][0]+'\n分數為'+str(round(self.candidate_dis[0][1],3))+'/'+str(len(self.symptoms))+'\n請問你還有其他症狀嗎？'
                response = '你看起來像有'+self.candidate_dis[0][0]+'\n' +'請問你還有其他症狀嗎？'
                return response, True
    
    def MONPA(self,text):
        result_pseg = monpa.pseg(text)
        monpa.load_userdict("server\MONPA_dictonary.txt")
        temp = []
        result = []
        result_list = []
        for item in result_pseg:
            # 抓採用詞性
            for pa in patterns:
                if pa in item:
                    temp.append(item)
        for i, item in enumerate(temp):
            word=()
            # 動詞判斷
            if item[1] in {'VA','VE'}: # 動詞自己就能表達意思 # 會在後面「取落單動詞」的部分被抓到
                word=item
                result.append(word)
                #result.append(temp[i][0])
            if item[1] in {'VB','VH','VHC'}: # 動作使動動詞 取前
                try:
                    if i-1 is not -1:
                        if temp[i-1][1]:
                            if temp[i-1][1] not in v_patterns:
                                word = (temp[i-1][0]+temp[i][0],temp[i-1][1]+'+'+temp[i][1])
                                # 如果出現副詞(NO)，把前面的單詞組合起來
                                if temp[i-1][1] in d_patterns:
                                    if result[-1] :
                                        word = (result[-1][0]+word[0], result[-1][1]+'+'+word[1]) 
                                        result[-1] = word
                                else:
                                    result.append(word)
                except:
                    continue
            if item[1] in {'VAC','VC','VF','VJ','VL'}: # 動作使動動詞 取後
                try:
                    if temp[i+1][1]:
                        if temp[i+1][1] not in v_patterns:
                            if temp[i+1][1] in d_patterns:
                                word = (temp[i][0],temp[i][1]) # 動詞後面是「不」，單放動詞進去
                                result.append(word)
                            else:
                                word = (temp[i][0]+temp[i+1][0],temp[i][1]+'+'+temp[i+1][1])
                                result.append(word)
                except:
                    continue
        # 把落單的動詞加進去
        for item in temp:
            word=0
            for con in result:
                if item[0] in con[0]:
                    word=1
            if word ==0 and item[1]!='NO': # 不採用落單的副詞
                result.append(item)
        for item in result:
            print(item)
            result_list.append(item[0])
        return result_list
    
    def MONPA_filter(self,queries):
        # seperate text
        queries = self.MONPA(queries)
        
        query_embeddings = self.embedder.encode(queries)
        threshold = 0.76
    
        # create empty disease dictionary
        result_list = []
        target_list = []
        valid_rate = []

        for query, query_embedding in zip(queries, query_embeddings):
            valid = False
            valid_count = 0
            max = 0
            highest_target = 'None'

            # iterate through disease
            for index, row in self.DataBase.iterrows():
                dists = scipy.spatial.distance.cdist([query_embedding], self.DataBase.loc[index,'symptoms_embeddings'], "cosine")[0]

                final_dist = 0
                avaliable_count = 0
                # iterate through symptom
                for index, dist in enumerate(dists):
                    if 1-dist >= threshold:
                        if 1-dist >= max:
                            highest_target = row['symptoms'][index]
                            max = 1-dist
                        valid = True
                        valid_count += 1
                        # break
                # if valid: break
            result_list.append(valid)
            target_list.append(highest_target)
            valid_rate.append(round(valid_count/271,2))
            if not valid:
                print(query, 'is invalid')
            else:
                print(query, 'is valid')
            # return result_list, target_list, valid_rate
        # do the filter
        answer = []
        for index, query_ in enumerate(queries):
            if result_list[index]:
                answer.append(query_)
        return answer
    
    def reset_inquiry(self):
        self.symptoms = []
        self.acupoints = []
        self.candidate_dis = []
    
    def load_DB(self):
        # DB settings
        print('reading database file...')
        self.DB_file_name = "server/disease_to_acu_and_symptom_modify_ZH_faceonly_embedding.csv"
        self.DataBase = None
        self.read_embedding_CSV()
        print('done!')
    
    def load_embedder(self):
        print('loading embedder...')
        self.embedder = SentenceTransformer('bert-base-chinese')
        print('done!')
            
    def __init__(self):        
        self.load_DB()
        self.load_embedder()
        
        # query settings
        self.query_return_number = 3
        self.query_threshold = 0.80
        self.candidate_dis = []
        
        # symptom list
        self.symptoms = []
        
        # acupoints list
        self.acupoints = []


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

# -------------------------------------------

if __name__ == '__main__':
    app.config['JSON_AS_ASCII'] = False
    app.run(host='0.0.0.0',port=3001)


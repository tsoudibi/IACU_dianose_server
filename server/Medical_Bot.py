#-*- encoding: UTF-8 -*-
print('starting server...')
import json
from flask import Flask, request
from flask import jsonify

# to use the service, server need to 'pip install -U sentence-transformers '
from sentence_transformers import SentenceTransformer
import scipy.spatial
from tqdm import tqdm
import ast
import pandas as pd
import monpa
from users_DB import USERS_DB
patterns=['Na','Nb','Nc','Ncd',
          'NO',
          'VA','VAC','VB','VC','VD','VE','VF','VG','VH','VHC','VI','VJ','VL']

n_patterns=['Na','Nb','Nc','Ncd']
d_patterns=['NO']
v_patterns=['VA','VAC','VB','VC','VD','VE','VF','VG','VH','VHC','VI','VJ','VL']

class Medical_Bot():
    # input: user input
    # output: response string, continue
    def inquiry(self, UID, input_symptoms_origin):
        self.UID = UID
        # load checkpoint
        self.symptoms,self.acupoints,self.candidate_dis = self.user_DB.load_checkpoint(self.UID)

        # do the MONPA
        input_symptoms = self.MONPA(input_symptoms_origin)

        # put the input_symptoms into symptoms list
        self.symptoms = self.symptoms + input_symptoms
        # query_disease
        self.candidate_dis = self.query_disease(self.symptoms)
        
        # get target disease, that is, the highest score candidate
        
        try:
            self.target_disease = self.candidate_dis[0][0]
            self.target_acupoint = self.DataBase.loc[self.DataBase['disease_name'] == self.target_disease]['acupoints'].to_list()[0]
        except:
            self.target_disease = []
            self.target_acupoint = []

        # save checkpoint
        self.user_DB.save_checkpoint(self.UID,
                                    self.symptoms,
                                    self.acupoints,
                                    self.candidate_dis)

        # check stop word
        # for stop_word in ["不", "沒", "否", "無"]:
        if '沒有症狀了' in input_symptoms_origin:
            # if there are candidate
            if len(self.candidate_dis) > 0:
                # response = '好的，你看起來像有'+self.candidate_dis[0][0]+'\n分數為'+str(round(self.candidate_dis[0][1],3))+'/'+str(len(self.symptoms))
                response = '以上症狀和「'+self.candidate_dis[0][0]+'」最匹配\n，推薦按摩的穴道為：'+self.target_acupoint[0]
                return response, False
            else:
                response = '好的，你真健康'
                return response, False
        
            
        
        if self.target_disease == []:
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
            response = '以上症狀和「'+self.candidate_dis[0][0]+'」最匹配\n' +'請提供更多症狀讓我判斷'
            return response, True


    # input: queried symptoms
    # output: 3 most possible disease
    def query_disease(self, queries):
        # encode quries
        query_embeddings = self.embedder.encode(queries)

        results = []
        
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
        # print("======================")
        print("Query:", queries)
        for name, distance in results[0:3]:
            print(name, "(Score: %.4f)" % (distance))
        
        # returning top 3 high result
        return results[0:self.query_return_number]
    

    # input: string of user input 
    # output: filtered symptoms
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
            # print(item)
            result_list.append(item[0])

        # filtering MONPA result
        symptoms = self.filtering_MONPA(result_list)

        return symptoms
    
    # input: symptoms after MONPA process
    # output: filtered symptoms
    def filtering_MONPA(self, MONPA_results):
        # encode MONPA_results
        query_embeddings = self.embedder.encode(MONPA_results)
        threshold = 0.76
    
        # create empty disease dictionary
        result_list = []
        target_list = []
        valid_rate = []

        # gothrough all MONPA_result
        for query, query_embedding in zip(MONPA_results, query_embeddings):
            valid = False
            valid_count = 0
            highest_socre = 0
            highest_target = 'None'

            # iterate through disease
            for index, row in self.DataBase.iterrows():
                dists = scipy.spatial.distance.cdist([query_embedding], self.DataBase.loc[index,'symptoms_embeddings'], "cosine")[0]
                # iterate through symptom
                for index, dist in enumerate(dists):
                    if 1-dist >= threshold:
                        if 1-dist >= highest_socre:
                            highest_target = row['symptoms'][index]
                            highest_socre = 1-dist
                        valid = True
                        valid_count += 1

            result_list.append(valid)
            target_list.append(highest_target)
            valid_rate.append(round(valid_count/271,2))
        print(MONPA_results)
        print(result_list)
        # filter out invalid symptoms
        answer = []
        for index, query_ in enumerate(MONPA_results):
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
    
    def load_embedder(self):
        print('loading embedder...')
        self.embedder = SentenceTransformer('bert-base-chinese')
        print('done!')
            
    def __init__(self, user_DB):        
        self.load_DB()
        self.load_embedder()

        self.user_DB = user_DB
        
        # query settings
        self.query_return_number = 3
        self.query_threshold = 0.80
        self.candidate_dis = []
        
        # symptom list
        self.symptoms = []
        
        # acupoints list
        self.acupoints = []
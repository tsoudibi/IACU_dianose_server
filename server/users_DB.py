# this python store all users log 
import json
from re import U

class USERS_DB():
    def __init__(self):
        try:
            json_file = open('server/users_log.json', 'r', encoding='utf-8')
            self.json_data = json.load(json_file) 
            print('load users DB successful!')

        except:
            print('no users DB found, creat new DB...')
            self.make_sample_file()
            json_file = open('server/users_log.json', 'r', encoding='utf-8')
            self.json_data = json.load(json_file) 
            print('load users DB successful!')
    
    def new_user(self, UID, USER_NAME):
        # iterate through json to find if it is new user
        is_new = True
        for user in self.json_data['user_list']:
            if user['UID'] == UID:
                is_new = False
                break
        if is_new:
            user = self.get_clean_user()
            user['UID'] = UID
            user['USER_NAME'] = USER_NAME
            self.json_data['user_list'].append(user)
            
            self.save_json()
            print('new user added!')

    def get_user_from_uid(self,UID):
        for user in self.json_data['user_list']:
            if user['UID'] == UID:
                return user
    
    def reset_checkpoint(self,UID):
        user = self.get_user_from_uid(UID)
        user['checkpoints']['symptoms'] = []
        user['checkpoints']['acupoints'] = []
        user['checkpoints']['candidate_dis'] = []

    # def save_response(self,UID,response):
    #     user = self.get_user_from_uid(UID)
    #     user['respones_logs'].append(response)
    #     self.save_json()
    
    # def save_answer(self,UID,answer):
    #     user = self.get_user_from_uid(UID)
    #     user['answers_logs'].append(answer)
    #     self.save_json()

    def save_checkpoint(self,UID,symptoms,acupoints,candidate_dis):
        user = self.get_user_from_uid(UID)
        user['checkpoints']['symptoms'] = symptoms
        user['checkpoints']['acupoints'] = acupoints
        user['checkpoints']['candidate_dis'] = candidate_dis
        self.save_json()

    def load_checkpoint(self,UID):
        user = self.get_user_from_uid(UID)
        return user['checkpoints']['symptoms'], user['checkpoints']['acupoints'], user['checkpoints']['candidate_dis'] 
    
    def save_json(self):
        with open('server/users_log.json', 'w', encoding='utf-8') as f:
            json.dump(self.json_data, f, indent=4,ensure_ascii = False)
    
    def get_clean_user(self):
        sample_user = {
            'UID':-1,
            'USER_NAME':'None',
            'answers_logs':[],
            'respones_logs':[],
            'checkpoints':{
                'symptoms':[],
                'acupoints':[],
                'candidate_dis':[]
            }
        }
        return sample_user
    
    def make_sample_file(self):
        sample_data = {}
        sample_data['user_list'] = []
        sample_data['user_list'].append(self.get_clean_user())
        with open('server/users_log.json', 'w') as f:
            json.dump(sample_data, f, indent=4)

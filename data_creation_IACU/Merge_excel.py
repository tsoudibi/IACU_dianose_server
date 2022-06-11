# -*- coding: utf-8 -*-
"""
Created on Thu Jan  7 12:52:45 2021

@author: USER
"""

import pandas as pd

#文件路径
dir='./'

#读取资料
df_sheet1=pd.read_excel(dir+'data-O.xlsx',engine='openpyxl',sheet_name='disease')
df_sheet2=pd.read_excel(dir+'data-O.xlsx',engine='openpyxl',sheet_name='acupoint')
df_sheet3=pd.read_excel(dir+'data-O.xlsx',engine='openpyxl',sheet_name='treatment')
#df=pd.read_excel(dir+'fininal_data.xlsx',engine='openpyxl')
df2=pd.read_excel(dir+'disease.xlsx',engine='openpyxl')

#添加表头便于检索
df_sheet1.head()
df_sheet2.head()
df_sheet3.head()
#df.head()
df2.head()

#测试是否读入资料
#print(df_sheet1['disease_name'])

#比对资料，并合并
cp_data=pd.merge(df_sheet3,df_sheet1,on='disease_ID')
#print(cp_data)

cp_data2=pd.merge(cp_data,df_sheet2,on='acupoint_ID')
#print(cp_data2)

cp_data3=pd.merge(cp_data2,df2,on='disease_name')
#print(cp_data3)

#cp=pd.merge(df, df2,on='disease_name')

#写入到新的excel中
#cp_data2.to_excel(r'C:/Users/USER/Desktop/data.xlsx',index=False)
cp_data3.to_excel(r'Merge_excel.xlsx',index=False)

# code borrowed from Oliver Kuperman
import requests
import random
import pandas as pd
from datetime import datetime
import time
import json 

N = 50 # max results per request for starter API
YEAR =  1999

with open('sensitive.json','r') as file:
    data = json.load(file)
    key = data['wos-key']

search_url = 'https://api.clarivate.com/apis/wos-starter/v1/documents'
headers = {'X-ApiKey':key}
params = {
    'db':'WOS',
    'q':f'PY={YEAR} AND SO=\"MED PHYS\"',
    'limit':N
}

response = requests.get(search_url,headers=headers,params=params)
data = response.json()
docs = data.get('hits',[])
print(docs)
# journal_docs = [doc for doc in docs if 'Article' in doc.get('types',[])]
# print(journal_docs)
import pandas as pd
import requests
import json

with open('sensitive.json','r') as file:
    data = json.load(file)
    EMAIL = data['email']


url = 'https://api.openalex.org/sources'
ids = []
names = []


whitelist_df = pd.read_csv('WOS comparisons/whitelist.csv')
for index, row in whitelist_df.iterrows():
    name = row['journal']
    names.append(name)
    
    
    issnl = row['issn-l']
    issne = row['issn-e']
    params = {
        'mailto':EMAIL,
        'filter':f'issn:{issnl}'
    }

    response = requests.get(url,params=params)
    print(response)
    if response.status_code == 404:
        params = {
            'mailto':EMAIL,
            'filter':f'issn:{issne}'
        }
        response = requests.get(url,params=params)
        if response.status_code == 404:
            ids.append(None)
            next
      
    result = response.json()
    results = result.get('results',[])
    if results:
        openalex_id = results[0]['id'].split('https://openalex.org/')[-1]
        ids.append(openalex_id)
        print(f'{name}: {openalex_id}')
    else:
        ids.append(None)


data = {
    'journal':names,
    'oa-id':ids
}

oa_df = pd.DataFrame(data)
merged_df = pd.merge(whitelist_df,oa_df,on='journal',how='inner')
merged_df.to_csv('whitelist.csv')
print(merged_df)
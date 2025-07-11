# test if the API has booted me or not

import requests
import json 

with open('sensitive.json','r') as file:
    data = json.load(file)
    EMAIL = data['email']

url = f'https://api.openalex.org/works/W2741809807'
params = {'mailto':EMAIL}

response = requests.get(url,params=params)
response.raise_for_status()
result = response.json()
print(result)
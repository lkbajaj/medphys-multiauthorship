import requests
import json 

with open('sensitive.json','r') as file:
    data = json.load(file)
    key = data['scopus-key']


url = "http://api.elsevier.com/content/search/scopus?query=heart"
headers = {"X-ELS-APIKey":key}
response = requests.get(url,headers=headers)
print(response.json())

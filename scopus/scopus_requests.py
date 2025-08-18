
import requests
import json 

YEAR = 1999
JOURNAL_NAME = "Physics in Medicine and Biology"

with open('sensitive.json','r') as file:
    data = json.load(file)
    key = data['scopus-key']

# headers is different than parameters. This is where you specify information like the key
headers = {
    "X-ELS-APIKey":key,
    "Accept":"application/json"
}

# initial query. Cursor will track how many results remaining, since search only allows quick 25 article bursts.
params = {
    'query': f'SRCTITLE("{JOURNAL_NAME}") AND DOCTYPE(ar) AND PUBYEAR = {YEAR}',
    'count': 1
}

all_entries = []
url = "http://api.elsevier.com/content/search/scopus"
response = requests.get(url,headers=headers,params=params)
data = response.json()

# loop through remaining cursors
entries = data.get('search-results',{}).get('entry',[])
all_entries.extend(entries)
print(all_entries)

# # keep repeating this process until there are no cursors left
# cursor = data['search-results'].get('cursor',{}).get('@next')
# while cursor: 
#     params['cursor'] = cursor 
#     response = requests.get(url, headers=headers, params=params)
#     entries = data.get('search-results',{}).get('entry',[])
#     all_entries.extend(entries)

#     # get the next cursor
#     cursor = data['search-results'].get('cursor',{}).get('@next')
    

# print(all_entries)
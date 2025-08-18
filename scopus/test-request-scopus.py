import requests
import json 

with open('sensitive.json','r') as file:
    data = json.load(file)
    key = data['scopus-key']

# sample scopus request
# url = "http://api.elsevier.com/content/search/scopus?query=heart"
# headers = {"X-ELS-APIKey":key}


# querying an article by id to get more info
SCOPUS_ID = '0032762229'
url = f"https://api.elsevier.com/content/abstract/scopus_id/{SCOPUS_ID}"
headers = {
    "X-ELS-APIKey": key,  # your API key
    "Accept": "application/json"
}
<<<<<<< Updated upstream

# get name of first author using Scopus
=======
>>>>>>> Stashed changes
response = requests.get(url,headers=headers)
data = response.json()
authors = data['abstracts-retrieval-response']['coredata']['dc:creator']['author']
first_author = authors[0]['ce:indexed-name']
first_author = first_author.split(' ')[1] + ' ' + first_author.split(' ')[0]
<<<<<<< Updated upstream

# get the DOI

# get the total number of citations
=======
print(first_author)
>>>>>>> Stashed changes

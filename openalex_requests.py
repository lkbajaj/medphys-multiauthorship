import requests
import time
import pandas as pd
import numpy as np
import json 

with open('sensitive.json','r') as file:
    data = json.load(file)
    EMAIL = data['email']

def combinejournaldicts(jdict1, jdict2):
    for key, value in jdict2.items():
        if key in jdict1:
            jdict1[key]['count'] += value.get('count', 0)
        else:
            jdict1[key] = value.copy()

# cursor method to get all papers, recommended by ChatGPT
def fetch_all_openalex_results(url,params,delay=0.5):
    params = params.copy()
    params['mailto'] = EMAIL
    params['cursor'] = '*'
    params['per_page'] = params.get('per-page',200)

    # limit queries to journals only
    if 'filter' not in params.keys():
        params['filter'] = 'primary_location.source.type:journal'
    else:
        params['filter'] = params['filter'] + ',primary_location.source.type:journal'

    while True:
        response = requests.get(url,params=params)
        response.raise_for_status()
        data = response.json()
        results = data.get('results',[])

        for item in results:
            yield item
        cursor = data.get('meta',{}).get('next_cursor')
        if not cursor:
            break

        params['cursor'] = cursor
        time.sleep(delay)

def get_citation_counts(work_id):
    # get year of the publication
    url = f'https://api.openalex.org/works/{work_id}'

    response = requests.get(url)
    response.raise_for_status()
    result = response.json()
    citations = result['cited_by_count']
    year = int(result['publication_year'])

    url = "https://api.openalex.org/works"
    params = {
        "filter":f"cites:{work_id}",
        "mailto":EMAIL
    }
    response = requests.get(url,params=params)
    response.raise_for_status()

    journaltracker = {}
    citations5yr = 0
    for work in fetch_all_openalex_results(url,params):
        source_id = work.get('primary_location').get('source',None)
        source_info = work.get('primary_location', {}).get('source', {})
        if source_id is not None:
            source_id = source_id.get('id',None)
        if source_id is not None:
            source_id = source_id.split('https://openalex.org/')[1]
            if source_id in journaltracker.keys():
                journaltracker[source_id]['count'] +=1
            else:
                journaltracker[source_id] = {
                    'count':1,
                    'name':source_info.get('display_name','')
                }
            
        pub_year = int(work.get("publication_year", None))
        if pub_year is not None:
            pub_year = int(pub_year) 
            if pub_year <= year + 5:
                citations5yr+=1
    

        
    return (citations,citations5yr,journaltracker)


# get publications from the Physics in Medicine and Biology journal from the year 2000
sourcedict = [
    {'name':'Physics in Medicine and Biology','id':'S20241394','year_start':1956,'year_end':2019},
    {'name':'Medical Physics','id':'S95522064'}
              ]
source_id  = sourcedict[0]['id']
source_name = sourcedict[0]['name']

YEAR_START=1957
YEAR_END=2019

years = np.arange(YEAR_START,YEAR_END+1)

source_tracker_main = {}

for year in years:
    year = int(year)
    url = 'https://api.openalex.org/works'
    params = {
        'filter':f'primary_location.source.id:{source_id},from_publication_date:{year}-01-01,to_publication_date:{year}-12-31',
        'per-page':200,
        'mailto':EMAIL
    }

    rows = []

    for work in fetch_all_openalex_results(url,params):
        name = work['display_name']
        alexid = work['id'][21:]
        doi = work.get('doi','')

        authorships = work.get('authorships',[])
        if authorships:
            first_author = authorships[0].get("author",{}).get('display_name')
            num_authors = len(authorships)
        else:
            first_author = ''
            num_authors = ''

        citations,citations5yrs,source_tracker_temp = get_citation_counts(alexid)
        combinejournaldicts(source_tracker_main,source_tracker_temp)
        
        rows.append({
            'title':name,
            'year':year,
            'first author':first_author,
            'total authors':num_authors,
            'doi':doi,
            'openalex_id':alexid,
            'total citations':citations,
            'citations_5yr':citations5yrs
        })

        print(rows[-1])

    dfauthorship = pd.DataFrame(rows)
    dfauthorship.to_csv(f'spreadsheets/authorship/{source_name}-{year}.csv',index=False)


    citationtrackerdf = pd.DataFrame.from_dict(source_tracker_main, orient='index')
    citationtrackerdf.index.name = 'id'  # Rename index to 'id' (was source_id)

    citationtrackerdf = citationtrackerdf.reset_index()
    citationtrackerdf.rename(columns={'name': 'journal name', 'count': 'citations'}, inplace=True)
    citationtrackerdf = citationtrackerdf[['journal name', 'id', 'citations']]

    citationtrackerdf = citationtrackerdf.sort_values(by='citations', ascending=False)

    citationtrackerdf.to_csv(f'spreadsheets/externaljournalcensus/CENSUS{source_name}-{year}.csv', index=False)

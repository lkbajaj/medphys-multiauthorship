import requests
import time
import pandas as pd
import numpy as np
import json 

# YEAR_START=1957
YEAR_START=2011
YEAR_END=2019
CURRENT_YEAR = 2025


with open('sensitive.json','r') as file:
    data = json.load(file)
    EMAIL = data['email']

whitelistdf = pd.read_csv('WOS comparisons/wos-dois/whitelist.csv')
whitelist_source_ids = list(whitelistdf['oa-id'].dropna())


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
        try:
            response = requests.get(url,params=params)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"request failed {e}")
            return e
        
        data = response.json()
        results = data.get('results',[])

        for item in results:
            yield item
        cursor = data.get('meta',{}).get('next_cursor')
        if not cursor:
            break

        params['cursor'] = cursor
        time.sleep(delay)

def get_citation_counts(work_id,curyear):
    # get year of the publication
    url = f'https://api.openalex.org/works/{work_id}'

    response = requests.get(url)
    response.raise_for_status()
    result = response.json()
    year = int(result['publication_year'])

    url = "https://api.openalex.org/works"
    params = {
        "filter":f"cites:{work_id}",
        "mailto":EMAIL
    }
    response = requests.get(url,params=params)
    response.raise_for_status()

    # journaltracker = {}
    citations5yr = 0
    citations = 0
    # new: make a year tracker and initialize it!
    year_tracker = {str(year): 0 for year in range(curyear,CURRENT_YEAR+1)}
    works = fetch_all_openalex_results(url,params)
    if isinstance(works, requests.exceptions.RequestException):
        return works
    for work in works:
        source_id = work.get('primary_location').get('source',None)
        if source_id is not None:
            source_id = source_id.get('id',None)
            if source_id is not None:
                source_id = source_id.split('/')[-1]
                pub_year = int(work.get("publication_year", None))
                if pub_year is not None:
                    pub_year = int(pub_year)
                    if source_id in whitelist_source_ids: # count only citations whose sources are in the whitelist
                        if pub_year >= curyear:
                            citations+=1
                            year_tracker[str(pub_year)] += 1
                            if pub_year <= year + 5:
                                citations5yr+=1
        
    return (citations,citations5yr,year_tracker)


# get publications from the Physics in Medicine and Biology journal from the year 2000
sourcedict = [
    {'name':'Physics in Medicine and Biology','id':'S20241394','year_start':1956},
    {'name':'Medical Physics','id':'S95522064','year_start':1974}
              ]
source_id  = sourcedict[1]['id']
source_name = sourcedict[1]['name']



years = np.arange(YEAR_START,YEAR_END+1)

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
        

        citationcounts = get_citation_counts(alexid,year)
        if isinstance(citationcounts, requests.exceptions.RequestException): # caught an exception. Go to the next one
            next

        citations,citations5yrs,citation_year_tracker = citationcounts
        
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

        rows[-1] = {**rows[-1],**citation_year_tracker}
        print(rows[-1])

    dfauthorship = pd.DataFrame(rows)
    print(dfauthorship)
    dfauthorship.to_csv(f'spreadsheets/authorship/{source_name}-{year}.csv',index=False)


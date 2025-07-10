import requests
import time
import pandas as pd
import numpy as np

# cursor method to get all papers, recommended by ChatGPT
def fetch_all_openalex_results(url,params,delay=0.5):
    params = params.copy()
    params['cursor'] = '*'
    params['per_page'] = params.get('per-page',200)

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
    year = int(result['publication_year'])

    url = "https://api.openalex.org/works"
    params = {
        "filter":f"cites:{work_id}"
    }
    response = requests.get(url,params=params)
    response.raise_for_status()

    results = response.json().get("results", [])

    citations = 0
    citations5yr = 0
    for work in fetch_all_openalex_results(url,params):
        pub_year = int(work.get("publication_year", None))
        if pub_year is not None:
            citations+=1
            pub_year = int(pub_year) 
            if pub_year <= year + 5:
                citations5yr+=1
    

        
    return (citations,citations5yr)


# get publications from the Physics in Medicine and Biology journal from the year 2000
sourcedict = {'Physics in Medicine and Biology':'S20241394'}
source_id  = sourcedict['Physics in Medicine and Biology']

YEAR_START=1956
YEAR_END=2019

years = np.arange(YEAR_START,YEAR_END+1)

for year in years:
    year = int(year)
    url = 'https://api.openalex.org/works'
    params = {
        'filter':f'primary_location.source.id:{source_id},from_publication_date:{year}-01-01,to_publication_date:{year}-12-31',
        'per-page':200
    }

    rows = []

    for work in fetch_all_openalex_results(url,params):
        name = work['display_name']
        alexid = work['id'][21:]

        authorships = work.get('authorships',[])
        if authorships:
            first_author = authorships[0].get("author",{}).get('display_name')
            num_authors = len(authorships)
        else:
            first_author = ''
            num_authors = ''
        citations,citations5yrs = get_citation_counts(alexid)
        
        rows.append({
            'title':name,
            'year':year,
            'first author':first_author,
            'total authors':num_authors,
            'openalex_id':alexid,
            'total citations':citations,
            'citations_5yr':citations5yrs
        })

        print(rows[-1])

    df = pd.DataFrame(rows)
    df.to_csv(f'spreadsheets/medphys-openalex{year}.csv',index=False)
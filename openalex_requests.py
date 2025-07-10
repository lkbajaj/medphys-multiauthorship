import requests
import time
import pandas as pd

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

YEAR_QUERY=2001

url = 'https://api.openalex.org/works'
params = {
    'filter':f'primary_location.source.id:{source_id},from_publication_date:{YEAR_QUERY}-01-01,to_publication_date:{YEAR_QUERY}-12-31',
    'per-page':200
}

rows = []

for work in fetch_all_openalex_results(url,params):
    name = work['display_name']
    alexid = work['id'][21:]

    authorships = work.get('authorships',[])
    if authorships:
        first_author = authorships[0].get("author",{}).get('display_name')
    else:
        first_author = ''
    citations,citations5yrs = get_citation_counts(alexid)
    
    rows.append({
        'title':name,
        'first author':first_author,
        'openalex_id':alexid,
        'total citations':citations,
        'citations_5yr':citations5yrs
    })

    print(rows[-1])

df = pd.DataFrame(rows)
df.to_csv(f'medphys-openalex{YEAR_QUERY}.csv',index=False)
import requests
import time
import pandas as pd
import numpy as np
import json

YEAR_START = 1999
YEAR_END = 2019
CURRENT_YEAR = 2025

with open('sensitive.json','r') as file:
    data = json.load(file)
    EMAIL = data['email']

whitelistdf = pd.read_csv('WOS comparisons/wos-dois/whitelist.csv')
# normalize whitelist IDs to strings
whitelist_source_ids = list(whitelistdf['oa-id'].dropna().astype(str).str.strip())
whitelist_source_ids_set = set(whitelist_source_ids)

def safe_get(url, params=None, timeout=30,retries=3,backoff=1.5):
    attempt = 0
    while True:
        try:
            r = requests.get(url, params=params,timeout=timeout)
            r.raise_for_status()
            return r
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            if status and 500 <= status < 600 and attempt < retries:
                attempt += 1
                time.sleep(backoff ** attempt)
                continue
            raise

def fetch_all_openalex_results(url, params, delay=0.5):
    params = params.copy()
    params['mailto'] = EMAIL
    params['cursor'] = '*'
    params['per_page'] = params.get('per-page', 200)  # tolerate your existing usage

    while True:
        try:
            response = safe_get(url, params=params)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"request failed {e}")
            break  # stop this stream gracefully

        data = response.json()
        for item in data.get('results', []):
            yield item

        cursor = data.get('meta', {}).get('next_cursor')
        if not cursor:
            break
        params['cursor'] = cursor
        time.sleep(delay)

def get_citation_counts(work_id, curyear, mode='default'):
    curyear = int(curyear)
    try:
    # focal (cited) work
        resp = safe_get(f'https://api.openalex.org/works/{work_id}', params={'mailto': EMAIL})
    except requests.exceptions.RequestException as e:
        return 0, 0, {str(y): 0 for y in range(int(curyear), CURRENT_YEAR+1)} # did not go through so the row will show as blank
    focal = resp.json()
    focal_pub_year = int(focal.get('publication_year'))

    # init counters
    citations = 0
    citations5yr = 0
    # safe init: ensure keys exist for any year we care about
    year_tracker = {str(y): 0 for y in range(curyear, CURRENT_YEAR + 1)}

    def update_trackers(citations, citations5yr, year_tracker, citing_year):
        if citing_year is None:
            return citations, citations5yr, year_tracker
        # count in window (reporting window uses curyear)
        if citing_year >= curyear:
            key = str(citing_year)
            # ensure key exists
            if key not in year_tracker:
                year_tracker[key] = 0
            citations += 1
            year_tracker[key] += 1
            # 5-year window relative to focal pub year
            if citing_year <= focal_pub_year + 5:
                citations5yr += 1
        return citations, citations5yr, year_tracker

    # iterate citing works via cursor; no preflight request needed
    url_cites = "https://api.openalex.org/works"
    params = {'filter': f'cites:{work_id}', 'mailto': EMAIL}

    for work in fetch_all_openalex_results(url_cites, params):
        py = work.get("publication_year")
        citing_year = int(py) if py is not None else None

        if mode == 'default':
            citations, citations5yr, year_tracker = update_trackers(citations, citations5yr, year_tracker, citing_year)

        elif mode == 'whitelist':
            src = (work.get('primary_location') or {}).get('source') or {}
            src_id_full = src.get('id')
            src_id = src_id_full.rsplit('/', 1)[-1] if src_id_full else None
            if src_id and src_id in whitelist_source_ids_set:
                citations, citations5yr, year_tracker = update_trackers(citations, citations5yr, year_tracker, citing_year)

        elif mode == 'scopus':
            # IMPORTANT: check the citing work, not the focal
            src = (work.get('primary_location') or {}).get('source') or {}
            in_scopus = src.get('is_indexed_in_scopus')
            if in_scopus:
                citations, citations5yr, year_tracker = update_trackers(citations, citations5yr, year_tracker, citing_year)

    return citations, citations5yr, year_tracker


sourcedict = [
    {'name':'Physics in Medicine and Biology','id':'S20241394','year_start':1956},
    {'name':'Medical Physics','id':'S95522064','year_start':1974},
    {'name':'Physica Medica','id':'S138998826'},  # corrected name
]
source_id  = sourcedict[1]['id']
source_name = sourcedict[1]['name']

years = np.arange(YEAR_START, YEAR_END + 1)

# new mode: read from WOS_PMB csv file
wos_article_df = pd.read_csv('WOS comparisons/wos-dois/WOS_MP_98_20.csv')
wos_article_df['year']  = wos_article_df['year'].astype(int)

for year in years:
    year = int(year)
    url = 'https://api.openalex.org/works'
    rows = []

    try:
        params = {
            'filter':f'primary_location.source.id:{source_id},from_publication_date:{year}-01-01,to_publication_date:{year}-12-31',
            'per-page':200,
            'mailto':EMAIL
        }
    
        works = fetch_all_openalex_results(url,params)


        for work in works:
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
            
            rows.append({
                'title':name,
                'year':year,
                'first author':first_author,
                'total authors':num_authors,
                'doi':doi,
                'openalex_id':alexid
            })

            print(rows[-1])
    
    except Exception as e:
        print(str(e))

    dfauthorship = pd.DataFrame(rows)
    print(dfauthorship)
    dfauthorship.to_csv(f'spreadsheets/authorship/MP/{source_name}-{year}.csv',index=False)




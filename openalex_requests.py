import requests
import time
import pandas as pd
import numpy as np
import json

YEAR_START = 2016
YEAR_END = 2020
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
    works = wos_article_df[wos_article_df['year'] == year].reset_index(drop=True)
    rows_all = []
    rows_whitelist = []
    rows_scopus = []
    try:
        for index,row in works.iterrows():
            doi = str(row['doi'])
            doi = 'https://doi.org/' + doi 
            url = 'https://api.openalex.org/works'
            params = {
                'filter':f'doi:{doi}',
                'per-page': 1,   # tolerated by fetcher (it copies into per_page)
                'mailto': EMAIL
            }
            try:
                for work in fetch_all_openalex_results(url, params):
                    name = work.get('display_name')
                    alexid = work.get('id', '')[21:]  # strip 'https://openalex.org/'
                    doi = work.get('doi', '')

                    authorships = work.get('authorships', []) or []
                    if authorships:
                        first_author = (authorships[0].get("author") or {}).get('display_name', '')
                        num_authors = len(authorships)
                    else:
                        first_author = ''
                        num_authors = ''

                    # One call per mode (you can refactor to one pass later)
                    citationcounts_all = get_citation_counts(alexid, year, mode='default')
                    citationcounts_whitelist = get_citation_counts(alexid, year, mode='whitelist')
                    citationcounts_scopus = get_citation_counts(alexid, year, mode='scopus')

                    def build_row(count_tuple):
                        citations, citations5yrs, tracker = count_tuple
                        base = {
                            'title': name,
                            'year': year,
                            'first author': first_author,
                            'total authors': num_authors,
                            'doi': doi,
                            'wos citations':row['citations'],
                            'openalex_id': alexid,
                            'total citations': citations,
                            'citations_5yr': citations5yrs,
                            'flag':''
                        }
                        base.update(tracker)
                        return base

                    rows_all.append(build_row(citationcounts_all))
                    print(rows_all[-1])
                    rows_whitelist.append(build_row(citationcounts_whitelist))
                    rows_scopus.append(build_row(citationcounts_scopus))
            except Exception as e:
                print(f'[ERROR] DOI failed: {doi}, {e}')
                # add an effectively empty citation data in this row to show that there was an exception
                base = {
                    'title': name,
                    'year': year,
                    'first author': first_author,
                    'total authors': num_authors,
                    'doi': doi,
                    'wos citations':row['citations'],
                    'openalex_id': '',
                    'total citations':'',
                    'citations_5yr':'',
                    'flag':repr(e)
                }

                tracker = {str(y): 0 for y in range(year, CURRENT_YEAR + 1)}
                base.update(tracker)
                rows_all.append(base)
                rows_whitelist.append(base)
                rows_scopus.append(base)
                
                            



        

        dfauthorship_all = pd.DataFrame(rows_all)
        dfauthorship_all.to_csv(f'spreadsheets/authorship/all/{source_name}-{year}.csv', index=False)

        dfauthorship_whitelist = pd.DataFrame(rows_whitelist)  # fixed
        dfauthorship_whitelist.to_csv(f'spreadsheets/authorship/whitelist/{source_name}-{year}.csv', index=False)

        dfauthorship_scopus = pd.DataFrame(rows_scopus)
        dfauthorship_scopus.to_csv(f'spreadsheets/authorship/scopus/{source_name}-{year}.csv', index=False)
    except Exception as e:
        print(f"[ERROR] Year {year} failed: {e}")
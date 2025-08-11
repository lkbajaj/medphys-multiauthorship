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

def fetch_all_openalex_results(url, params, delay=0.5):
    params = params.copy()
    params['mailto'] = EMAIL
    params['cursor'] = '*'
    params['per_page'] = params.get('per-page', 200)  # tolerate your existing usage

    while True:
        try:
            response = requests.get(url, params=params)
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

    # focal (cited) work
    resp = requests.get(f'https://api.openalex.org/works/{work_id}', params={'mailto': EMAIL})
    resp.raise_for_status()
    focal = resp.json()
    focal_pub_year = int(focal.get('publication_year'))

    # init counters
    citations = 0
    citations5yr = 0
    # safe init: ensure keys exist for any year we care about
    start_for_tracker = min(curyear, focal_pub_year)
    year_tracker = {str(y): 0 for y in range(start_for_tracker, CURRENT_YEAR + 1)}

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

# --- main loop ---
sourcedict = [
    {'name':'Physics in Medicine and Biology','id':'S20241394','year_start':1956},
    {'name':'Medical Physics','id':'S95522064','year_start':1974},
    {'name':'Physica Medica','id':'S138998826'},  # corrected name
]
source_id  = sourcedict[0]['id']
source_name = sourcedict[0]['name']

years = np.arange(YEAR_START, YEAR_END + 1)

for year in years:
    year = int(year)
    url = 'https://api.openalex.org/works'
    params = {
        'filter': f'primary_location.source.id:{source_id},from_publication_date:{year}-01-01,to_publication_date:{year}-12-31',
        'per-page': 200,   # tolerated by fetcher (it copies into per_page)
        'mailto': EMAIL
    }

    rows_all = []
    rows_whitelist = []
    rows_scopus = []

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

        if not isinstance(citationcounts_all, requests.exceptions.RequestException):
            citations, citations5yrs, citation_year_tracker = citationcounts_all
            rows_all.append({
                'title': name,
                'year': year,
                'first author': first_author,
                'total authors': num_authors,
                'doi': doi,
                'openalex_id': alexid,
                'total citations': citations,
                'citations_5yr': citations5yrs
            })
            rows_all[-1] = {**rows_all[-1],**citation_year_tracker}
            print(rows_all[-1])

        if not isinstance(citationcounts_whitelist, requests.exceptions.RequestException):
            citations, citations5yrs, citation_year_tracker = citationcounts_whitelist
            rows_whitelist.append({
                'title': name,
                'year': year,
                'first author': first_author,
                'total authors': num_authors,
                'doi': doi,
                'openalex_id': alexid,
                'total citations': citations,
                'citations_5yr': citations5yrs
            })
            rows_whitelist[-1] = {**rows_whitelist[-1],**citation_year_tracker}

          

        if not isinstance(citationcounts_scopus, requests.exceptions.RequestException):
            citations, citations5yrs, citation_year_tracker = citationcounts_scopus
            rows_scopus.append({
                'title': name,
                'year': year,
                'first author': first_author,
                'total authors': num_authors,
                'doi': doi,
                'openalex_id': alexid,
                'total citations': citations,
                'citations_5yr': citations5yrs
            })
            rows_scopus[-1] = {**rows_scopus[-1],**citation_year_tracker}

     

    dfauthorship_all = pd.DataFrame(rows_all)
    dfauthorship_all.to_csv(f'spreadsheets/authorship/all/{source_name}-{year}.csv', index=False)

    dfauthorship_whitelist = pd.DataFrame(rows_whitelist)  # fixed
    dfauthorship_whitelist.to_csv(f'spreadsheets/authorship/whitelist/{source_name}-{year}.csv', index=False)

    dfauthorship_scopus = pd.DataFrame(rows_scopus)
    dfauthorship_scopus.to_csv(f'spreadsheets/authorship/scopus/{source_name}-{year}.csv', index=False)

import pandas as pd
import numpy as np
from rapidfuzz import process, fuzz

JOURNAL_TITLE = 'Medical Physics'
JOURNAL_TITLE_ABR= 'MP'
YEAR_START = 1999
YEAR_END= 2019
CURRENT_YEAR = 2025

MATCH_THRESHOLD = 97

file_dir = f'spreadsheets/authorship/{JOURNAL_TITLE_ABR}'
wos_file = f'WOS comparisons/wos-dois/WOS_{JOURNAL_TITLE_ABR}_98_20.csv'
output_excel_file = f'spreadsheets/outputs-final/{JOURNAL_TITLE_ABR}_WOSmerged_{YEAR_START}-{YEAR_END}.xlsx'

wos_df = pd.read_csv(wos_file)

 
# prepare wos dataframe for the merge
wos_df['doi'] = ('https://doi.org/' + wos_df['doi'].astype(str)).str.lower() # add the beginning of the doi link so it matches with openalex that tracks the links
wos_df = wos_df.rename(columns={'year':'wos_year','citations':'wos_citations','title':'wos_title'}) # rename the wos columns to differentiate them from the openalex ones
wos_df = wos_df.drop(columns=['source.pages.count','authors','number.authors']) # get rid of extraneous columns

wos_df = wos_df.add_prefix("wos_")
wos_df = wos_df.rename(columns={"wos_doi": "doi"})  # keep join key clean

with pd.ExcelWriter(output_excel_file, engine='xlsxwriter') as writer:
    for year in range(YEAR_START,YEAR_END+1):
        oa_df = pd.read_csv(f'{file_dir}/{JOURNAL_TITLE}-{year}.csv')

        # prepare openalex dataframe for merge
        oa_df = oa_df.rename(columns={'year':'openalex_year','title':'openalex_title','total citations':'openalex_citations'})
        oa_df['doi'] = oa_df['doi'].str.lower()
        oa_df = oa_df.add_prefix("openalex_")

        oa_df = oa_df.rename(columns={"openalex_doi": "doi"})  # keep join key clean
        
        merged_df = pd.merge(wos_df, oa_df, on="doi", how="inner")

        order = ['openalex_openalex_year','wos_wos_year','openalex_openalex_title','wos_wos_title','openalex_first author','openalex_total authors','doi','openalex_openalex_id','wos_wos_citations']
        merged_df = merged_df[order]
        merged_df = merged_df.rename(columns = {'wos_wos_year':'wos_year',
                                                'wos_wos_title':'wos_title',
                                                'wos_wos_citations':'wos_citations',
                                                'openalex_first author':'first_author',
                                                'openalex_total authors':'total authors',
                                                'openalex_openalex_id':'openalex_id',
                                                'openalex_openalex_title':'openalex_title',
                                                'openalex_openalex_year':'openalex_year'})

       
        print(merged_df)
        merged_df.to_excel(writer,sheet_name=str(year),index=False)






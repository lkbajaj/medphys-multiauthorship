import pandas as pd
import numpy as np
import os
import openpyxl

JOURNAL_TITLE = 'Physics in Medicine and Biology'
JOURNAL_TITLE_ABR= 'PMB'
YEAR_START = 1999
YEAR_END= 2019

file_dir = f'spreadsheets/authorship/{JOURNAL_TITLE_ABR}'
wos_file = f'WOS comparisons/wos-dois/WOS_PMB_98_20.csv'
output_excel_file = f'spreadsheets/outputs-final/{JOURNAL_TITLE_ABR}merged_{YEAR_START}-{YEAR_END}.xlsx'

wos_df = pd.read_csv(wos_file)
 
# prepare wos dataframe for the merge
wos_df['doi'] = 'https://doi.org/' + wos_df['doi'].astype(str) # add the beginning of the doi link so it matches with openalex that tracks the links
wos_df = wos_df.rename(columns={'year':'wos_year','citations':'wos_citations','title':'wos_title'}) # rename the wos columns to differentiate them from the openalex ones
wos_df = wos_df.drop(columns=['source.pages.count','authors','number.authors']) # get rid of extraneous columns

with pd.ExcelWriter(output_excel_file, engine='xlsxwriter') as writer:
    for year in range(YEAR_START,YEAR_END+1):
        openalex_df = pd.read_csv(f'{file_dir}/{JOURNAL_TITLE}-{year}.csv')

        # prepare openalex dataframe for merge
        openalex_df = openalex_df.rename(columns={'year':'openalex_year','title':'openalex_title','total citations':'openalex_citations'})

        merged_df = pd.merge(wos_df,openalex_df,on='doi',how='inner') # do the merge
        merged_df = merged_df[['openalex_year','wos_year','openalex_title','wos_title','first author','total authors','doi','openalex_id','openalex_citations','wos_citations','citations_5yr']] # specify the ordering of the final dataframe
        merged_df.to_excel(writer,sheet_name=str(year),index=False)





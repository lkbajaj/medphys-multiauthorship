import pandas as pd
import numpy as np
from rapidfuzz import process, fuzz


JOURNAL_TITLE = 'Physics in Medicine and Biology'
JOURNAL_TITLE_ABR= 'PMB'
YEAR_START = 1999
YEAR_END= 2019
CURRENT_YEAR = 2025

MATCH_THRESHOLD = 99

file_dir = f'spreadsheets/authorship/{JOURNAL_TITLE_ABR}'
wos_file = f'WOS comparisons/wos-dois/WOS_{JOURNAL_TITLE_ABR}_98_20.csv'
output_excel_file = f'spreadsheets/outputs-final/{JOURNAL_TITLE_ABR}merged_{YEAR_START}-{YEAR_END}_CI.xlsx'

wos_df = pd.read_csv(wos_file)

 
# prepare wos dataframe for the merge
wos_df['doi'] = ('https://doi.org/' + wos_df['doi'].astype(str)).str.lower() # add the beginning of the doi link so it matches with openalex that tracks the links
wos_df = wos_df.rename(columns={'year':'wos_year','citations':'wos_citations','title':'wos_title'}) # rename the wos columns to differentiate them from the openalex ones
wos_df = wos_df.drop(columns=['source.pages.count','authors','number.authors']) # get rid of extraneous columns

with pd.ExcelWriter(output_excel_file, engine='xlsxwriter') as writer:
    for year in range(YEAR_START,YEAR_END+1):
        oa_df = pd.read_csv(f'{file_dir}/{JOURNAL_TITLE}-{year}.csv')

        # prepare openalex dataframe for merge
        oa_df = oa_df.rename(columns={'year':'openalex_year','title':'openalex_title','total citations':'openalex_citations'})
        oa_df['doi'] = oa_df['doi'].str.lower()

        matched_rows = []
        
        for i, wos_row in wos_df.iterrows():
            wos_doi = wos_row['doi']

            match_result = process.extractOne(
                wos_doi,
                oa_df['doi'],
                scorer = fuzz.ratio
            )

            if match_result:
                matched_doi, score, match_index = match_result
                if score >= MATCH_THRESHOLD:
                    oa_row = oa_df.loc[match_index]
                    combined = pd.concat([wos_row.add_prefix('wos_'),oa_row])
                    matched_rows.append(combined)

        merged_df = pd.DataFrame(matched_rows)
        order = ['openalex_year','wos_wos_year','openalex_title','wos_wos_title','first author','total authors','doi','openalex_id','openalex_citations','wos_wos_citations','citations_5yr']
        years_citations = np.arange(year,CURRENT_YEAR+1).astype(str).tolist()
        order.extend(years_citations)
        merged_df = merged_df[order]
        merged_df = merged_df.rename(columns = {'wos_wos_year':'wos_year','wos_wos_title':'wos_title','wos_wos_citations':'wos_citations'})
        print(merged_df)
        merged_df.to_excel(writer,sheet_name=str(year),index=False)






import pandas as pd
import numpy as np
import os
import openpyxl

JOURNAL_TITLE = 'Physics in Medicine and Biology'
JOURNAL_TITLE_ABR= 'PMB'
YEAR = 2016 

file_dir = f'spreadsheets/authorship/{JOURNAL_TITLE_ABR}/'
wos_file_dir = f'WOS comparisons/{JOURNAL_TITLE_ABR}/'
output_dir = f'spreadsheets/outputs-final/merged/'


wos_files = sorted(
    [f for f in os.listdir(wos_file_dir)],
    key=lambda name: int(name.split('_')[-1].split('.')[0])
)

for file in wos_files:
    # open a WoS file and put relevant parameters (doi,title) into a new dataframe
    year = file.split('_')[-1].split('.')[0]
    file_ext = file.split('_')[-1].split('.')[1] # usually .xls but sometimes .xlsx or .xlsm

    df1 = pd.read_excel(f'WOS comparisons/PMB/PMB_wos_{year}.{file_ext}')
    doi = np.asarray(df1['DOI'])
    doi = 'https://doi.org/' + doi

    title = df1['Article Title']
    data = {
        'WoS title':title,
        'doi':doi,
    }

    df1 = pd.DataFrame(data)

    # get the relevant openalex csv into its own df and merge the two
    df2 = pd.read_csv(f'{file_dir}{JOURNAL_TITLE}-{year}.csv')
    merged_df = pd.merge(df1,df2,on='doi',how='inner').reset_index(drop=True)
    merged_df.rename(columns={'title':'openalex title'},inplace=True)
    merged_df.to_csv(f'{output_dir}{JOURNAL_TITLE_ABR}-MERGED-{year}.csv',index=False)

output_excel = f'spreadsheets/outputs-final/{JOURNAL_TITLE_ABR}-MERGED.xlsx'

with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
    merged_files = sorted(
    [f for f in os.listdir(output_dir) if 'cashe' not in f],
    key=lambda name: int(name.split('-')[-1].split('.')[0])
    )

    for i in range(len(merged_files)):
        file = f'{output_dir}{merged_files[i]}'
        year = int(file.split('-')[-1].split('.')[0])

        if i == 0:
            year_start = year
        elif i == len(merged_files)-1:
            year_end = year
        
        df = pd.read_csv(file)
        df.to_excel(writer,sheet_name=str(year),index=False)
        # delete to avoid clutter and contamination from previous runs
        if 'cashe' not in file:
            os.remove(file)

    os.rename(output_excel,f'spreadsheets/outputs-final/{JOURNAL_TITLE_ABR}_MERGED_{year_start}-{year_end}.xlsx')   
        

        





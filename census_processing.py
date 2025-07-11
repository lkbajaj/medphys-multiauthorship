import requests
import os
import pandas as pd
import json

with open('sensitive.json','r') as file:
    data = json.load(file)
    EMAIL = data['email']

# first start by replacing the ids with display names
csv_folder = 'spreadsheets/externaljournalcensus/'
output_excel = 'PMBcitationstracking.xlsx'

# sort the file names first
csv_files = sorted(
    [f for f in os.listdir(csv_folder) if f.endswith('.csv')],
    key=lambda name: int(name.split('-')[-1].split('.')[0])
)

year_start = 9999
year_end = 9999

with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
    for i in range(len(csv_files)):
        filename = csv_files[i]
 
        if filename.endswith('.csv'):
            file_path = os.path.join(csv_folder,filename)
            year = int(os.path.splitext(filename)[0].split('-')[-1])
            print(year)

            if i == 0:
                year_start = year
            elif i == len(csv_files)-1:
                year_end = year
            
            df = pd.read_csv(file_path)
            journal_name = list(df['journal name'])
            id = list(df['id'])
            citations = list(df['citations'])

            data = {
                'journal_name':journal_name,
                'id':id,
                'citations':citations
            }
            dfnew = pd.DataFrame(data)
            dfnew.to_excel(writer,sheet_name=str(year),index=False)

os.rename(output_excel,f'CITATIONJOURNALTRACKER_{year_start}-{year_end}.xlsx')

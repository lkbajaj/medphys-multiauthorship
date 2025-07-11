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
            spreadsheetfilename = f'CITATIONJOURNALTRACKER_{year_start}-{year_end}.xlsx'

os.rename(output_excel,spreadsheetfilename)

sources_net = {}
with pd.ExcelWriter('PMBnetcitations.xlsx', engine='xlsxwriter') as writer:
    for i in range(len(csv_files)):
        df = pd.read_csv(file_path)
        for index,row in df.iterrows():
            journal_id = row['id']
            citations = row['citations']

            # initialize or add to dictionary 
            if journal_id in sources_net.keys():
                sources_net[journal_id]['citations'] += citations 
            else: 
                name = row['journal name']
                sources_net[journal_id] = {'journal name':name,'citations':citations}
    

    citationtrackerdf = pd.DataFrame.from_dict(sources_net, orient='index')
    citationtrackerdf.index.name = 'id'  # Rename index to 'id' (was source_id)

    citationtrackerdf = citationtrackerdf.reset_index()
    citationtrackerdf.rename(columns={'name': 'journal name', 'count': 'citations'}, inplace=True)
    citationtrackerdf = citationtrackerdf[['journal name', 'id', 'citations']]

    citationtrackerdf = citationtrackerdf.sort_values(by='citations', ascending=False)

    citationtrackerdf.to_excel(writer,sheet_name='net',index=False)
    

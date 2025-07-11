import pandas as pd
import os

csv_folder = 'spreadsheets/authorship/'
output_excel = 'PMBcombo.xlsx'

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
            df.to_excel(writer,sheet_name=str(year),index=False)


os.rename(output_excel,f'PMBcombo_{year_start}-{year_end}.xlsx')

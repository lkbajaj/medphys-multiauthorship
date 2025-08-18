import pandas as pd
import os

# UPDATE TO MERGE FUNCTIONALITY. ALLOW MERGE FROM 1999-2019 timescale for PMB

JOURNAL_NAME = 'PMB'
JOURNAL_NAME_FULL = 'Physics in Medicine and Biology'

csv_folder = 'spreadsheets/authorship/scopus'
output_excel = f'spreadsheets/outputs-final/{JOURNAL_NAME}combo.xlsx'

# sort the file names first
csv_files = sorted(
    [f for f in os.listdir(csv_folder) if f.endswith('.csv') and f.split('-')[0] == JOURNAL_NAME_FULL],
    key=lambda name: int(name.split('-')[-1].split('.')[0])
)


year_start = 1999
year_end = 2019

with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
    for i in range(len(csv_files)):
        filename = csv_files[i]
 
        if filename.endswith('.csv'):
            file_path = os.path.join(csv_folder,filename)
            year = int(os.path.splitext(filename)[0].split('-')[-1])
            if year <= year_end and year >= year_start:
                df = pd.read_csv(file_path)
                df.to_excel(writer,sheet_name=str(year),index=False)


os.rename(output_excel,f'spreadsheets/outputs-final/{JOURNAL_NAME}combo_{year_start}-{year_end}_SCP.xlsx')

# csv_folder = 'spreadsheets/authorship/whitelist'
# output_excel = f'spreadsheets/outputs-final/{JOURNAL_NAME}combo.xlsx'

# # sort the file names first
# csv_files = sorted(
#     [f for f in os.listdir(csv_folder) if f.endswith('.csv') and f.split('-')[0] == JOURNAL_NAME_FULL],
#     key=lambda name: int(name.split('-')[-1].split('.')[0])
# )


# with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
#     for i in range(len(csv_files)):
#         filename = csv_files[i]
 
#         if filename.endswith('.csv'):
#             file_path = os.path.join(csv_folder,filename)
#             year = int(os.path.splitext(filename)[0].split('-')[-1])
#             if year <= year_end and year >= year_start:
#                 df = pd.read_csv(file_path)
#                 df.to_excel(writer,sheet_name=str(year),index=False)


# os.rename(output_excel,f'spreadsheets/outputs-final/{JOURNAL_NAME}combo_{year_start}-{year_end}_WHT.xlsx')

# csv_folder = 'spreadsheets/authorship/all'
# output_excel = f'spreadsheets/outputs-final/{JOURNAL_NAME}combo.xlsx'

# # sort the file names first
# csv_files = sorted(
#     [f for f in os.listdir(csv_folder) if f.endswith('.csv') and f.split('-')[0] == JOURNAL_NAME_FULL],
#     key=lambda name: int(name.split('-')[-1].split('.')[0])
# )

# with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
#     for i in range(len(csv_files)):
#         filename = csv_files[i]
 
#         if filename.endswith('.csv'):
#             file_path = os.path.join(csv_folder,filename)
#             year = int(os.path.splitext(filename)[0].split('-')[-1])
#             if year <= year_end and year >= year_start:
#                 df = pd.read_csv(file_path)
#                 df.to_excel(writer,sheet_name=str(year),index=False)


# os.rename(output_excel,f'spreadsheets/outputs-final/{JOURNAL_NAME}combo_{year_start}-{year_end}_ALL.xlsx')
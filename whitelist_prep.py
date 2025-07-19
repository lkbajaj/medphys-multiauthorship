import pandas as pd

file_dir_wos =  'WOS comparisons/WOS_Core_Science_Journals_List_SCIE+ESCI.xlsx'

# there are two excel worksheets: one for WOS SCIE and another for the ESCI list
dfSCIE =  pd.read_excel(file_dir_wos,sheet_name=0)
dfESCIE = pd.read_excel(file_dir_wos,sheet_name=1)

# merge them
dfmerged = pd.concat([dfSCIE,dfESCIE])

data = {
    'journal':list(dfmerged['Journal title']),
    'issn-l':list(dfmerged['ISSN']),
    'issn-e':list(dfmerged['eISSN']),
    'categories':list(dfmerged['Web of Science Categories'])
}

dfmerged = pd.DataFrame(data)
dfmerged.to_csv('WOS comparisons/whitelist.csv',index=False)

import pandas as pd
EXCEL_WOS_FILE = 'WOS comparisons/wos-dois/WOS_MedicalPhysics_98_20.xlsx'
OUTPUT_DIR = 'WOS comparisons/wos-dois/WOS_MP_98_20.csv'

sheet_names = pd.ExcelFile(EXCEL_WOS_FILE).sheet_names
all_sheets = [pd.read_excel(EXCEL_WOS_FILE,sheet_name=sheet) for sheet in sheet_names]
combined_df = pd.concat(all_sheets,ignore_index=True)
combined_df.to_csv(OUTPUT_DIR,index=False)
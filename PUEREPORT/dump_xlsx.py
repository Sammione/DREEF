import pandas as pd

def get_xlsx_info(path):
    # Try multiple headers to see where data starts
    xls = pd.ExcelFile(path)
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet_name, header=None)
        # Drop completely empty rows and columns for cleaner view
        df = df.dropna(how='all').dropna(axis=1, how='all')
        print(f"Sheet: {sheet_name}")
        print(df.head(50).to_csv(index=False))

get_xlsx_info('sheet 1.xlsx')

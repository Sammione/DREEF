import pandas as pd
import io

def find_header_and_peek(path):
    df_raw = pd.read_excel(path, header=None)
    for i, row in df_raw.iterrows():
        row_values = [str(x).lower() for x in row if pd.notna(x)]
        if any('community' in x or 'state' in x or 'name' in x for x in row_values):
            print(f"Potential header at row {i}: {row_values}")
            df = pd.read_excel(path, header=i)
            print("Columns:", df.columns.tolist())
            print("First 3 rows of data:")
            print(df.head(3).to_string())
            return
    print("No header found with expected keywords.")
    print("Raw first 10 rows:")
    print(df_raw.head(10).to_string())

find_header_and_peek('sheet 1.xlsx')

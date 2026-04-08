import pandas as pd
import io

def peek_excel(path):
    print(f"Peeking {path}")
    df = pd.read_excel(path, header=None, nrows=20)
    print(df.to_string())

peek_excel('sheet 1.xlsx')

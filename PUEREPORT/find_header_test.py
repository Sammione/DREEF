import pandas as pd
import io

def find_best_header(path):
    for i in range(10):
        df = pd.read_excel(path, header=i).head(5)
        cols = [str(c).lower() for c in df.columns]
        if any(k in " ".join(cols) for k in ['community', 'state', 'lga', 'name', 'coordinate', 'latitude']):
            print(f"Index {i}: {df.columns.tolist()}")
            return i
    return 0

idx = find_best_header('sheet 1.xlsx')
df = pd.read_excel('sheet 1.xlsx', header=idx)
print(f"Dumping first 5 rows with header {idx}:")
print(df.head(5).to_markdown())

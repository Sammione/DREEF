
import pandas as pd
from docx import Document
import re

def analyze_structure():
    print("ANALYSIS START")
    
    # Excel Analysis
    try:
        # Read header=None to see raw data first
        df = pd.read_excel('sheet 1.xlsx', header=None, nrows=10)
        print("\n--- Excel Raw First 5 Rows ---")
        print(df.head(5).to_string())
        
        # Try to guess header row
        header_row_idx = 0
        for i, row in df.iterrows():
            # If row has "Community" or "Location" or similar, it's likely the header
            row_str = " ".join([str(val) for val in row.values])
            if "Community" in row_str or "Location" in row_str:
                header_row_idx = i
                break
        
        print(f"\nGuessed Header Row Index: {header_row_idx}")
        df_proper = pd.read_excel('sheet 1.xlsx', header=header_row_idx)
        print(f"Columns found: {list(df_proper.columns)}")
        
    except Exception as e:
        print(f"Excel Error: {e}")

    # Docx Analysis
    try:
        doc = Document('PUE report templat- Copy.docx')
        text = "\n".join([p.text for p in doc.paragraphs])
        
        # Find [Placeholder]
        bracket_matches = re.findall(r'\[(.*?)\]', text)
        print(f"\n--- Docx Bracket Placeholders Found ({len(bracket_matches)}) ---")
        unique_brackets = sorted(list(set(bracket_matches)))
        for m in unique_brackets:
            print(f"[{m}]")
            
        # Find specific words mentioned
        print("\n--- Context Check ---")
        if "Location" in text:
            print("'Location' word found in text.")

    except Exception as e:
        print(f"Docx Error: {e}")

if __name__ == "__main__":
    analyze_structure()

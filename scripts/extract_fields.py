"""
=============================================================================
SCRIPT NAME: extract_fields.py
=============================================================================

INPUT FILES:
- Production Data/Bloomberg Master Field List.xlsx: Bloomberg field catalog

OUTPUT FILES:
- (prints to stdout)

VERSION: 1.0
LAST UPDATED: 2026-04-27
AUTHOR: AI Assistant

DESCRIPTION:
Reads Column B (all data items/field mnemonics) from the Bloomberg Master Field List
and prints them all for analysis.

DEPENDENCIES:
- pandas, openpyxl

USAGE:
cd /Users/arjundivecha/Dropbox/AAA\ Backup/A\ Working/BloombergGPT
python scripts/extract_fields.py
=============================================================================
"""

import pandas as pd
import sys
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parent.parent / "Production Data" / "Bloomberg Master Field List.xlsx"

def main():
    # First check what sheets are available
    xls = pd.ExcelFile(CATALOG_PATH)
    print(f"Sheet names: {xls.sheet_names}", file=sys.stderr)

    # Read each sheet
    for sheet in xls.sheet_names:
        df = pd.read_excel(CATALOG_PATH, sheet_name=sheet)
        print(f"\n=== Sheet: {sheet} ===", file=sys.stderr)
        print(f"Columns: {list(df.columns)}", file=sys.stderr)
        print(f"Shape: {df.shape}", file=sys.stderr)

    # Read the main sheet (likely "Pruned List") and extract column B
    SHEET_NAME = "Pruned List"
    df = pd.read_excel(CATALOG_PATH, sheet_name=SHEET_NAME)

    # Column B is the second column (index 1)
    col_b_name = df.columns[1]
    print(f"\nColumn B name: '{col_b_name}'", file=sys.stderr)

    # Extract all non-null values from Column B
    fields = df.iloc[:, 1].dropna().tolist()
    fields = [str(f).strip() for f in fields if str(f).strip()]
    fields = sorted(set(fields))  # deduplicate and sort

    print(f"\nTotal unique field mnemonics: {len(fields)}", file=sys.stderr)
    
    for i, f in enumerate(fields, 1):
        print(f)

if __name__ == "__main__":
    main()

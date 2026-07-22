"""
=============================================================================
SCRIPT NAME: test_shares_fields.py
=============================================================================

DESCRIPTION:
    Tests different Bloomberg field names for ETF shares outstanding
    using the EEM ETF. Evaluates 6 candidate fields such as
    FUND_TOTAL_SHARES_OUTSTANDING, SHARES_OUTSTANDING, EQY_SH_OUT,
    etc., and reports which ones return valid data.

INPUT FILES:
    (none — no file I/O)

OUTPUT FILES:
    (none — no file I/O)

VERSION: 1.0
LAST UPDATED: 2026-06-05
AUTHOR: Arjun Divecha

DEPENDENCIES:
    - OpusBloomberg (local library at .../OpusBloomberg)
    - blpapi

USAGE:
    python test_shares_fields.py

NOTES:
    - Requires Bloomberg Terminal to be open and logged in
    - Tests 6 candidate field names for shares outstanding
=============================================================================
"""
import sys
sys.path.insert(0, "/Users/arjundivecha/Dropbox/AAA Backup/A Working/OpusBloomberg")

from bbg import BBG, bloomberg_setup
from datetime import datetime

# Set up Bloomberg connection
print("Setting up Bloomberg connection...")
bloomberg_setup(verbose=False)

ticker = "EEM US Equity"
start_date = "2026-04-01"
end_date = datetime.today().strftime("%Y-%m-%d")

# Test different field names for shares outstanding
candidate_fields = [
    "FUND_TOTAL_SHARES_OUTSTANDING",
    "SHARES_OUTSTANDING",
    "EQY_SH_OUT",
    "FUND_SHARES_OUT",
    "OUTSTANDING_SHARES",
    "TOT_SHR_OUT",
]

print(f"\nTesting field names for {ticker}...")
print(f"Date range: {start_date} to {end_date}\n")

with BBG() as bbg:
    for field in candidate_fields:
        try:
            start_yyyymmdd = start_date.replace("-", "")
            end_yyyymmdd = end_date.replace("-", "")
            
            hist_data = bbg.hist(ticker, field, start_yyyymmdd, end_yyyymmdd)
            
            if hist_data and any(point.get(field) is not None for point in hist_data):
                print(f"✓ {field}: WORKING")
                print(f"  Sample values: {[point.get(field) for point in hist_data[:3]]}")
            else:
                print(f"✗ {field}: No data")
        except Exception as e:
            print(f"✗ {field}: Error - {e}")

print("\nTest complete.")

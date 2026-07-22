"""
=============================================================================
SCRIPT NAME: test_eem.py
=============================================================================

DESCRIPTION:
    Tests Bloomberg connection by fetching historical and reference data
    for the EEM ETF (iShares MSCI Emerging Markets ETF). Uses the
    OpusBloomberg library to retrieve shares outstanding, NAV, and
    total assets data.

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
    python test_eem.py

NOTES:
    - Requires Bloomberg Terminal to be open and logged in
    - Uses OpusBloomberg library for Bloomberg connectivity
=============================================================================
"""
import sys
sys.path.insert(0, "/Users/arjundivecha/Dropbox/AAA Backup/A Working/OpusBloomberg")

from bbg import BBG, bloomberg_setup
from datetime import datetime

# Set up Bloomberg connection
print("Setting up Bloomberg connection...")
try:
    bloomberg_setup(verbose=True)
    print("Bloomberg connection ready.")
except Exception as e:
    print(f"Warning: Bloomberg setup failed: {e}")
    print("Continuing anyway...")

# Test with EEM only
ticker = "EEM US Equity"
start_date = "2026-01-01"
end_date = datetime.today().strftime("%Y-%m-%d")

print(f"\nTesting historical data for {ticker}...")
print(f"Date range: {start_date} to {end_date}")

with BBG() as bbg:
    # Test historical data
    fields = ["EQY_SH_OUT", "FUND_NET_ASSET_VAL", "FUND_TOTAL_ASSETS"]
    start_yyyymmdd = start_date.replace("-", "")
    end_yyyymmdd = end_date.replace("-", "")
    
    hist_data = bbg.hist(ticker, fields, start_yyyymmdd, end_yyyymmdd)
    
    print(f"\nRetrieved {len(hist_data)} data points")
    if hist_data:
        print("Sample data:")
        for point in hist_data[:3]:
            print(f"  {point.get('date')}: shares={point.get('EQY_SH_OUT')}, nav={point.get('FUND_NET_ASSET_VAL')}, aum={point.get('FUND_TOTAL_ASSETS')}")
    else:
        print("No data retrieved")
    
    # Test reference data
    print(f"\nTesting reference data for {ticker}...")
    ref_data = bbg.ref(ticker, ["NAME", "FUND_TOTAL_ASSETS"])
    print(f"Reference data: {ref_data}")

print("\nTest complete.")

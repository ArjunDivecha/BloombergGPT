"""
=============================================================================
SCRIPT NAME: test_nasdaq_etff.py
=============================================================================

DESCRIPTION:
    Tests access to the Nasdaq Data Link (formerly Quandl) ETFF database
    for the INDA ETF. Validates the API key, checks which databases are
    accessible, and attempts to fetch ETF fund flow data from the ETFF
    database.

INPUT FILES:
    (none — no file I/O)

OUTPUT FILES:
    (none — no file I/O)

VERSION: 1.0
LAST UPDATED: 2026-06-05
AUTHOR: Arjun Divecha

DEPENDENCIES:
    - requests
    - pandas

USAGE:
    python test_nasdaq_etff.py

NOTES:
    - Requires a Nasdaq Data Link API key (embedded in script)
    - ETFF database requires a paid subscription
=============================================================================
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
import os

# Try the key without any spaces
API_KEY = "d6Rn6rWxBbQXxj4Ub88u"
BASE_URL = "https://data.nasdaq.com/api/v3/datasets"

def test_api_key():
    """Test if the API key is valid and what access it has"""
    print(f"\n{'='*60}")
    print("Testing API Key validity and permissions")
    print('='*60)
    print(f"API Key being used: '{API_KEY}'")
    
    # Try different authentication methods
    methods = [
        ("Query parameter", {"api_key": API_KEY}, {}),
        ("Header", {}, {"X-Api-Key": API_KEY}),
        ("Bearer token", {}, {"Authorization": f"Bearer {API_KEY}"}),
    ]
    
    for method_name, params, headers in methods:
        print(f"\nTrying {method_name}...")
        try:
            url = f"{BASE_URL}/WIKI/AAPL"
            all_params = {"rows": 1}
            all_params.update(params)
            
            response = requests.get(url, params=all_params, headers=headers, timeout=10)
            print(f"  Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  ✓ Success with {method_name}!")
                return True
            elif response.status_code == 403:
                print(f"  ✗ 403 Forbidden - Incapsula blocking or invalid key")
            elif response.status_code == 404:
                print(f"  ✗ 404 Not found")
            else:
                print(f"  ✗ Failed: {response.text[:100]}")
                
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
    
    return False

def test_etff_access():
    """Test accessing the ETFF database for INDA"""
    
    # ETFF dataset code for US ETF Fund Flows
    # The dataset code is typically "ETFF/{TICKER}" or similar
    # Let's try a few variations
    
    test_codes = [
        "ETFF/INDA",
        "NASDAQ/ETFF_INDA",
        "QUANDL/ETFF_INDA",
    ]
    
    for code in test_codes:
        print(f"\n{'='*60}")
        print(f"Testing dataset code: {code}")
        print('='*60)
        
        try:
            url = f"{BASE_URL}/{code}"
            params = {
                "api_key": API_KEY,
                "start_date": (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
                "end_date": datetime.now().strftime("%Y-%m-%d"),
                "order": "desc",
                "limit": 10
            }
            
            response = requests.get(url, params=params, timeout=10)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Success! Dataset found.")
                print(f"Dataset Name: {data.get('dataset', {}).get('name', 'N/A')}")
                print(f"Column Names: {data.get('dataset', {}).get('column_names', [])}")
                print(f"Data Points: {len(data.get('dataset', {}).get('data', []))}")
                
                # Show first few rows
                df = pd.DataFrame(data.get('dataset', {}).get('data', []), 
                                 columns=data.get('dataset', {}).get('column_names', []))
                print("\nSample data:")
                print(df.head())
                
                return True, code, data
            elif response.status_code == 403:
                print(f"✗ Access forbidden (likely requires paid subscription)")
            elif response.status_code == 404:
                print(f"✗ Dataset not found")
            else:
                print(f"✗ Failed: {response.text[:200]}")
                
        except Exception as e:
            print(f"✗ Error: {str(e)}")
    
    return False, None, None

def check_database_access():
    """Check what databases are accessible with this API key"""
    print(f"\n{'='*60}")
    print("Checking database access")
    print('='*60)
    
    # List of common databases to check
    databases = ["WIKI", "FRED", "ETFF", "NSE", "EOD"]
    
    for db in databases:
        try:
            print(f"\nChecking {db}...")
            # Try to get a simple dataset from each database
            url = f"{BASE_URL}/{db}/.metadata"
            params = {"api_key": API_KEY}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                print(f"  ✓ {db} is accessible")
            elif response.status_code == 403:
                print(f"  ✗ {db} - Access forbidden (likely requires paid subscription)")
            elif response.status_code == 404:
                print(f"  ✗ {db} - Not found")
            else:
                print(f"  ✗ {db} - Status {response.status_code}")
                
        except Exception as e:
            print(f"  ✗ {db} - Error: {str(e)}")

if __name__ == "__main__":
    print("Testing Nasdaq Data Link ETFF Access for INDA")
    print(f"API Key: {API_KEY}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # First test if the API key is valid
    api_valid = test_api_key()
    
    if api_valid:
        # Check what databases are accessible
        check_database_access()
        
        # Try to access ETFF for INDA
        print("\n" + "="*60)
        print("Attempting to access ETFF for INDA")
        print("="*60)
        success, code, data = test_etff_access()
        
        if not success:
            print("\n" + "="*60)
            print("CONCLUSION")
            print("="*60)
            print("The ETFF database requires a paid subscription.")
            print("Your current API key does not have access to this database.")
            print("You would need to upgrade your Nasdaq Data Link subscription")
            print("to access ETF fund flow data.")
    else:
        print("\n✗ API key appears to be invalid. Please check your key.")

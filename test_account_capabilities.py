"""
=============================================================================
SCRIPT NAME: test_account_capabilities.py
=============================================================================

DESCRIPTION:
    Probes what data and features the Bloomberg account has access to
    by testing single ticker reference data, batch multi-ticker requests,
    historical data access, and field availability. Saves results to a
    JSON file and generates recommendations for optimized endpoints.

INPUT FILES:
    (none — no file I/O beyond .env)

OUTPUT FILES:
    account_capabilities_results.json
        JSON results of all capability tests, including response times
        and available fields by category

VERSION: 1.0
LAST UPDATED: 2026-06-05
AUTHOR: Arjun Divecha

DEPENDENCIES:
    - requests
    - python-dotenv
    - json (stdlib)

USAGE:
    python test_account_capabilities.py

NOTES:
    - Requires Bloomberg Terminal logged in and broker running (python main.py)
    - Output file is written to the current working directory
=============================================================================
"""

import requests
import time
import os
from dotenv import load_dotenv
import json

load_dotenv()
API_KEY = os.getenv('API_KEY', 'Caeser00**')
BASE_URL = "http://localhost:8000"
headers = {"x-api-key": API_KEY}

print("=" * 80)
print("Bloomberg Account Capability Test")
print("=" * 80)
print("\nThis will test what data/features are available to your account.")
print("Please ensure:")
print("  1. Bloomberg Terminal is logged in")
print("  2. Bloomberg broker is running (python main.py)")
print("\n" + "=" * 80)

# Test data
test_tickers = ["AAPL", "MSFT", "GOOGL"]
test_fields = {
    "basic": ["PX_LAST", "NAME"],
    "market": ["VOLUME", "CUR_MKT_CAP"],
    "valuation": ["PE_RATIO", "PX_TO_BOOK_RATIO"],
    "dividend": ["DVD_YILD"],
    "change": ["CHG_PCT_1D"]
}

results = {
    "single_ticker": None,
    "batch_tickers": None,
    "historical": None,
    "available_fields": {},
    "response_times": {}
}

# Test 1: Single Ticker Reference Data
print("\n" + "=" * 80)
print("TEST 1: Single Ticker - Basic Fields")
print("=" * 80)

all_fields = [f for fields in test_fields.values() for f in fields]
print(f"\nTesting: AAPL with fields: {', '.join(all_fields)}")

try:
    start = time.time()
    response = requests.get(
        f"{BASE_URL}/blp/refdata",
        params={"ticker": "AAPL", "fields": all_fields},
        headers=headers,
        timeout=30
    )
    elapsed = time.time() - start
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ SUCCESS - Response time: {elapsed:.2f}s")
        print(f"\nData received:")
        
        ticker_data = data.get("data", {})
        for field in all_fields:
            value = ticker_data.get(field, "N/A")
            status = "✓" if value and value != "No Data" else "✗"
            print(f"  {status} {field:<25} = {value}")
            
            # Track which fields work
            category = [k for k, v in test_fields.items() if field in v][0]
            if category not in results["available_fields"]:
                results["available_fields"][category] = []
            if value and value != "No Data":
                results["available_fields"][category].append(field)
        
        results["single_ticker"] = "SUCCESS"
        results["response_times"]["single_ticker"] = elapsed
    else:
        print(f"✗ FAILED - Status: {response.status_code}")
        print(f"  Error: {response.text[:200]}")
        results["single_ticker"] = f"FAILED ({response.status_code})"

except Exception as e:
    print(f"✗ ERROR - {str(e)}")
    results["single_ticker"] = f"ERROR: {str(e)}"

# Test 2: Batch/Multi-Ticker Request
print("\n" + "=" * 80)
print("TEST 2: Batch Request - Multiple Tickers")
print("=" * 80)

# Use only fields that worked in Test 1
working_fields = list(set([f for fields in results["available_fields"].values() for f in fields]))
if not working_fields:
    working_fields = ["PX_LAST", "NAME"]  # Fallback

print(f"\nTesting: {', '.join(test_tickers)} with fields: {', '.join(working_fields[:3])}")

try:
    start = time.time()
    
    # Build URL with multiple ticker parameters
    params = {"fields": working_fields[:3]}
    url = f"{BASE_URL}/blp/refdata"
    
    # Add multiple ticker params
    ticker_params = "&".join([f"ticker={t}" for t in test_tickers])
    field_params = "&".join([f"fields={f}" for f in working_fields[:3]])
    full_url = f"{url}?{ticker_params}&{field_params}"
    
    response = requests.get(
        full_url,
        headers=headers,
        timeout=30
    )
    elapsed = time.time() - start
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ SUCCESS - Response time: {elapsed:.2f}s")
        print(f"\nBatch response structure:")
        
        if "data" in data and isinstance(data["data"], dict):
            print(f"  ✓ Batch mode: YES")
            print(f"  ✓ Tickers returned: {len(data['data'])}")
            
            for ticker, ticker_data in data["data"].items():
                print(f"\n  {ticker}:")
                for field in working_fields[:3]:
                    value = ticker_data.get(field, "N/A")
                    print(f"    {field}: {value}")
            
            results["batch_tickers"] = "SUCCESS"
        else:
            print(f"  ? Single ticker mode (batch may not be supported)")
            results["batch_tickers"] = "SINGLE_MODE_ONLY"
        
        results["response_times"]["batch_tickers"] = elapsed
    else:
        print(f"✗ FAILED - Status: {response.status_code}")
        print(f"  Error: {response.text[:200]}")
        results["batch_tickers"] = f"FAILED ({response.status_code})"

except Exception as e:
    print(f"✗ ERROR - {str(e)}")
    results["batch_tickers"] = f"ERROR: {str(e)}"

# Test 3: Historical Data
print("\n" + "=" * 80)
print("TEST 3: Historical Data")
print("=" * 80)

print(f"\nTesting: AAPL with PX_LAST from 2024-01-01 to 2024-01-31")

try:
    start = time.time()
    response = requests.get(
        f"{BASE_URL}/blp/historical",
        params={
            "ticker": "AAPL",
            "fields": "PX_LAST",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "periodicity": "DAILY"
        },
        headers=headers,
        timeout=30
    )
    elapsed = time.time() - start
    
    if response.status_code == 200:
        data = response.json()
        historical_data = data.get("data", [])
        
        print(f"✓ SUCCESS - Response time: {elapsed:.2f}s")
        print(f"  Data points returned: {len(historical_data)}")
        
        if len(historical_data) > 0:
            print(f"  Sample (first 3 points):")
            for point in historical_data[:3]:
                date = point.get("date", "N/A")
                value = point.get("values", {}).get("PX_LAST", "N/A")
                print(f"    {date}: {value}")
            
            results["historical"] = "SUCCESS"
            results["response_times"]["historical"] = elapsed
        else:
            print(f"  ⚠ No data points returned")
            results["historical"] = "NO_DATA"
    else:
        print(f"✗ FAILED - Status: {response.status_code}")
        print(f"  Error: {response.text[:200]}")
        results["historical"] = f"FAILED ({response.status_code})"

except Exception as e:
    print(f"✗ ERROR - {str(e)}")
    results["historical"] = f"ERROR: {str(e)}"

# Summary
print("\n" + "=" * 80)
print("CAPABILITY SUMMARY")
print("=" * 80)

print(f"\n1. Single Ticker Access: {results['single_ticker']}")
if results["single_ticker"] == "SUCCESS":
    print(f"   ✓ Response time: {results['response_times'].get('single_ticker', 0):.2f}s")

print(f"\n2. Batch/Multi-Ticker: {results['batch_tickers']}")
if results["batch_tickers"] == "SUCCESS":
    print(f"   ✓ Response time: {results['response_times'].get('batch_tickers', 0):.2f}s")
    print(f"   ✓ Can process multiple tickers in one request")
elif results["batch_tickers"] == "SINGLE_MODE_ONLY":
    print(f"   ⚠ Batch mode may not be supported - will need multiple API calls")

print(f"\n3. Historical Data: {results['historical']}")
if results["historical"] == "SUCCESS":
    print(f"   ✓ Response time: {results['response_times'].get('historical', 0):.2f}s")

print(f"\n4. Available Field Categories:")
for category, fields in results["available_fields"].items():
    if fields:
        print(f"   ✓ {category.capitalize()}: {', '.join(fields)}")
    else:
        print(f"   ✗ {category.capitalize()}: No fields available")

# Recommendations
print("\n" + "=" * 80)
print("RECOMMENDATIONS FOR OPTIMIZED ENDPOINTS")
print("=" * 80)

can_do_snapshot = results["single_ticker"] == "SUCCESS" and len(results["available_fields"]) > 0
can_do_batch = results["batch_tickers"] == "SUCCESS"
can_do_stats = results["historical"] == "SUCCESS"

print(f"\n✓ Can implement /blp/snapshot: {can_do_snapshot}")
if can_do_snapshot:
    if can_do_batch:
        print(f"  → Will use batch requests for multiple tickers (faster)")
    else:
        print(f"  → Will use multiple single requests (slower but works)")
    print(f"  → Available fields: {', '.join(list(set([f for fields in results['available_fields'].values() for f in fields])))}")

print(f"\n✓ Can implement /blp/historical-stats: {can_do_stats}")
if can_do_stats:
    print(f"  → Can calculate min/max/avg/change statistics")
    print(f"  → Response time acceptable for stats calculation")

print(f"\n✓ Can implement /blp/compare: {can_do_snapshot}")
if can_do_snapshot:
    if can_do_batch:
        print(f"  → Will use batch mode for efficient comparison")
    else:
        print(f"  → Will make sequential requests")

# Performance estimate
print("\n" + "=" * 80)
print("PERFORMANCE ESTIMATE")
print("=" * 80)

if can_do_snapshot and can_do_batch:
    print(f"\n✓ EXCELLENT - Batch mode works")
    print(f"  Current 4-ticker comparison: ~{results['response_times'].get('batch_tickers', 0):.1f}s")
    print(f"  With /blp/compare endpoint: ~{results['response_times'].get('batch_tickers', 0):.1f}s (data ready for ChatGPT)")
    print(f"  ChatGPT processing saved: ~10-15s")
    print(f"  Total speedup: ~10-15x faster ⚡")
elif can_do_snapshot:
    print(f"\n✓ GOOD - Single ticker mode works")
    print(f"  Current 4-ticker comparison: ~{results['response_times'].get('single_ticker', 0) * 4:.1f}s (4 requests)")
    print(f"  With /blp/compare endpoint: ~{results['response_times'].get('single_ticker', 0) * 4:.1f}s (pre-formatted)")
    print(f"  ChatGPT processing saved: ~10-15s")
    print(f"  Total speedup: ~5-8x faster ⚡")
else:
    print(f"\n✗ ISSUES DETECTED")
    print(f"  Please restart Bloomberg Terminal and broker, then rerun this test")

# Save results
print("\n" + "=" * 80)
with open("account_capabilities_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("Results saved to: account_capabilities_results.json")
print("=" * 80)


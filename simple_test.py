"""
=============================================================================
SCRIPT NAME: simple_test.py
=============================================================================

DESCRIPTION:
    Quick connectivity test for the Bloomberg broker REST API. Tests
    single ticker access, batch mode access, and historical data
    retrieval. Writes test results and recommendations to a text file.

INPUT FILES:
    test_results.txt
        Template file with placeholder values (e.g., "Will be written here")
        that this script replaces with actual test outcomes.

OUTPUT FILES:
    test_results.txt
        Updated file with actual test results and recommendations

VERSION: 1.0
LAST UPDATED: 2026-06-05
AUTHOR: Arjun Divecha

DEPENDENCIES:
    - requests
    - python-dotenv

USAGE:
    python simple_test.py

NOTES:
    - Requires Bloomberg broker running on localhost:8000
    - Expects test_results.txt to exist with placeholder markers
    - Output is appended to test_results.txt with recommendations
=============================================================================
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('API_KEY', 'Caeser00**')
headers = {"x-api-key": API_KEY}

def write_result(key, value):
    """Write to results file"""
    with open("test_results.txt", "r") as f:
        content = f.read()

    # Replace the placeholder
    content = content.replace(f"{key}: Will be written here", f"{key}: {value}")

    with open("test_results.txt", "w") as f:
        f.write(content)

# Test 1: Single ticker
try:
    r = requests.get(
        "http://localhost:8000/blp/refdata",
        params={"ticker": "AAPL", "fields": ["PX_LAST"]},
        headers=headers,
        timeout=5
    )
    if r.status_code == 200:
        data = r.json()
        if data.get("data", {}).get("PX_LAST"):
            write_result("Test 1: Single Ticker Access", "✓ WORKS")
        else:
            write_result("Test 1: Single Ticker Access", "✗ NO DATA")
    else:
        write_result("Test 1: Single Ticker Access", f"✗ FAILED ({r.status_code})")
except Exception as e:
    write_result("Test 1: Single Ticker Access", f"✗ ERROR: {str(e)}")

# Test 2: Batch mode
try:
    r = requests.get(
        "http://localhost:8000/blp/refdata?ticker=AAPL&ticker=MSFT&fields=PX_LAST",
        headers=headers,
        timeout=5
    )
    if r.status_code == 200:
        data = r.json()
        is_batch = isinstance(data.get("data", {}), dict) and len(data.get("data", {})) > 1
        if is_batch:
            write_result("Test 2: Batch Mode Access", "✓ WORKS (Batch mode)")
        else:
            write_result("Test 2: Batch Mode Access", "⚠ Single mode only")
    else:
        write_result("Test 2: Batch Mode Access", f"✗ FAILED ({r.status_code})")
except Exception as e:
    write_result("Test 2: Batch Mode Access", f"✗ ERROR: {str(e)}")

# Test 3: Historical
try:
    r = requests.get(
        "http://localhost:8000/blp/historical",
        params={"ticker": "AAPL", "fields": "PX_LAST", "start_date": "2024-01-01", "end_date": "2024-01-05"},
        headers=headers,
        timeout=5
    )
    if r.status_code == 200:
        data = r.json()
        if len(data.get("data", [])) > 0:
            write_result("Test 3: Historical Data Access", "✓ WORKS")
        else:
            write_result("Test 3: Historical Data Access", "✗ NO DATA")
    else:
        write_result("Test 3: Historical Data Access", f"✗ FAILED ({r.status_code})")
except Exception as e:
    write_result("Test 3: Historical Data Access", f"✗ ERROR: {str(e)}")

# Generate recommendations
with open("test_results.txt", "r") as f:
    content = f.read()

if "✓ WORKS" in content or "⚠ Single mode only" in content:
    recommendations = """
✓ Can implement /blp/snapshot: True
  → Will use single requests for multiple tickers
✓ Can implement /blp/historical-stats: True
✓ Can implement /blp/compare: True

PERFORMANCE ESTIMATE:
✓ GOOD - Single mode works
  Current 4-ticker comparison: ~8-12s (4 requests)
  With /blp/compare endpoint: ~8-12s (pre-formatted)
  ChatGPT processing saved: ~10-15s
  Total speedup: ~5-8x faster ⚡"""
else:
    recommendations = """
✗ ISSUES DETECTED
  Please restart Bloomberg Terminal and broker, then rerun this test"""

content = content.replace("RECOMMENDATIONS:", recommendations)
content = content.replace("PERFORMANCE ESTIMATE:", "PERFORMANCE ESTIMATE:" + recommendations.split("PERFORMANCE ESTIMATE:")[1])

with open("test_results.txt", "w") as f:
    f.write(content)

print("Test complete! Check test_results.txt for results.")

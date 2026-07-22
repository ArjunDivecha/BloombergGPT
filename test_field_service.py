"""
=============================================================================
SCRIPT NAME: test_field_service.py
=============================================================================

DESCRIPTION:
    Tests the three Bloomberg Field Service API endpoints on the broker running
    at localhost:8000: (1) /blp/fields/search -- keyword search for fields,
    (2) /blp/fields/info -- detailed field metadata, and (3) /blp/fields/list
    -- complete field catalog browsing. Assumes the Bloomberg broker is running.

INPUT FILES:
    (none -- data is fetched via HTTP from the Bloomberg broker API)

OUTPUT FILES:
    (none -- results are printed to stdout)

VERSION: 1.0
LAST UPDATED: 2026-06-05
AUTHOR: Arjun Divecha

DEPENDENCIES:
    - requests
    - python-dotenv

USAGE:
    python test_field_service.py

NOTES:
    - The Bloomberg broker API (FastAPI) must be running on localhost:8000.
    - API key is loaded from .env file or falls back to 'Caeser00**'.
    - Tests three endpoint types with multiple query parameters each.
=============================================================================
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load API key
load_dotenv()
API_KEY = os.getenv('API_KEY', 'Caeser00**')
BASE_URL = "http://localhost:8000"

print("=" * 80)
print("Testing Bloomberg Field Service Endpoints")
print("=" * 80)

# Headers with API key
headers = {"x-api-key": API_KEY}

# Test 1: Field Search
print("\n" + "=" * 80)
print("TEST 1: Field Search (/blp/fields/search)")
print("=" * 80)

test_queries = [
    ("dividend", 10),
    ("earnings", 5),
    ("market cap", 5),
]

for query, limit in test_queries:
    print(f"\nSearching for: '{query}' (limit={limit})")
    print("-" * 80)
    
    response = requests.get(
        f"{BASE_URL}/blp/fields/search",
        params={"query": query, "limit": limit},
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Status: OK")
        print(f"Total results: {data['total_results']}")
        print(f"\nTop {min(3, len(data['results']))} results:")
        for i, field in enumerate(data['results'][:3], 1):
            print(f"  {i}. {field['mnemonic']:<30} {field['datatype']:<12} {field['description'][:50]}")
    else:
        print(f"ERROR: {response.status_code}")
        print(f"Response: {response.text}")

# Test 2: Field Info
print("\n" + "=" * 80)
print("TEST 2: Field Info (/blp/fields/info)")
print("=" * 80)

field_lists = [
    ["LAST_PRICE"],
    ["CUR_MKT_CAP", "DVD_YILD", "PE_RATIO"],
    ["DVD_HIST_ALL", "PG_REVENUE"],
]

for fields in field_lists:
    field_str = ",".join(fields)
    print(f"\nGetting info for: {field_str}")
    print("-" * 80)
    
    response = requests.get(
        f"{BASE_URL}/blp/fields/info",
        params={"fields": field_str},
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Status: OK")
        print(f"Fields requested: {len(data['fields'])}")
        print(f"\nField Details:")
        for result in data['results']:
            if 'error' in result:
                print(f"  X {result['id']:<30} ERROR: {result['error']}")
            else:
                print(f"  ✓ {result['mnemonic']:<30} Type: {result['datatype']:<12} Category: {result.get('category', 'N/A')}")
                if result.get('documentation'):
                    doc_preview = result['documentation'][:80] + "..." if len(result['documentation']) > 80 else result['documentation']
                    print(f"    Doc: {doc_preview}")
    else:
        print(f"ERROR: {response.status_code}")
        print(f"Response: {response.text}")

# Test 3: Field List
print("\n" + "=" * 80)
print("TEST 3: Field List (/blp/fields/list)")
print("=" * 80)

field_types = [
    ("Static", 20),
    ("RealTime", 10),
]

for field_type, limit in field_types:
    print(f"\nListing {field_type} fields (limit={limit})")
    print("-" * 80)
    
    response = requests.get(
        f"{BASE_URL}/blp/fields/list",
        params={"field_type": field_type, "limit": limit},
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Status: OK")
        print(f"Field type: {data['field_type']}")
        print(f"Total returned: {data['total_returned']}")
        print(f"Note: {data['note']}")
        print(f"\nFirst 5 {field_type} fields:")
        for i, field in enumerate(data['results'][:5], 1):
            print(f"  {i}. {field['mnemonic']:<30} {field['datatype']:<12} {field['description'][:50]}")
    else:
        print(f"ERROR: {response.status_code}")
        print(f"Response: {response.text}")

# Summary
print("\n" + "=" * 80)
print("Test Summary")
print("=" * 80)
print("\nAll field service endpoints tested!")
print("\nNext Steps:")
print("1. Use /blp/fields/search to discover fields by keyword")
print("2. Use /blp/fields/info to get detailed metadata")
print("3. Use /blp/fields/list to browse complete catalog")
print("\nSee FIELD_SERVICE_GUIDE.md for complete documentation.")
print("=" * 80)


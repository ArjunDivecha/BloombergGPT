"""
=============================================================================
SCRIPT NAME: test_field_service_quick.py
=============================================================================

DESCRIPTION:
    Quick health check for all 3 field service endpoints (Field Search,
    Field Info, Field List). Sends HTTP GET requests to localhost:8000
    and reports pass/fail for each endpoint.

INPUT FILES:
    (none — no file I/O)

OUTPUT FILES:
    (none — no file I/O)

VERSION: 1.0
LAST UPDATED: 2026-06-05
AUTHOR: Arjun Divecha

DEPENDENCIES:
    - requests
    - python-dotenv

USAGE:
    python test_field_service_quick.py

NOTES:
    - Requires Bloomberg broker running on localhost:8000
    - Uses API_KEY from .env file (defaults to Caeser00**)
=============================================================================
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('API_KEY', 'Caeser00**')
BASE_URL = "http://localhost:8000"
headers = {"x-api-key": API_KEY}

print("=" * 60)
print("Field Service Quick Health Check")
print("=" * 60)

tests = [
    ("Field Search", "GET", f"{BASE_URL}/blp/fields/search", {"query": "dividend", "limit": 3}),
    ("Field Info", "GET", f"{BASE_URL}/blp/fields/info", {"fields": "LAST_PRICE"}),
    ("Field List", "GET", f"{BASE_URL}/blp/fields/list", {"field_type": "Static", "limit": 5}),
]

results = []
for name, method, url, params in tests:
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            result_count = len(data.get('results', []))
            print(f"\n✓ {name:<20} OK - Returned {result_count} results")
            results.append(True)
        else:
            print(f"\n✗ {name:<20} FAILED - Status {response.status_code}")
            print(f"  Error: {response.text[:100]}")
            results.append(False)
    except Exception as e:
        print(f"\n✗ {name:<20} ERROR - {str(e)}")
        results.append(False)

print("\n" + "=" * 60)
if all(results):
    print("✓ All Field Service endpoints are working!")
else:
    print(f"✗ {sum(results)}/{len(results)} tests passed")
print("=" * 60)


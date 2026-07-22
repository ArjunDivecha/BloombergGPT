"""
=============================================================================
SCRIPT NAME: test_field_search_now.py
=============================================================================

DESCRIPTION:
    Tests the field search endpoint of the Bloomberg broker service by
    sending search queries (e.g., "last price", "PX_LAST", "market cap")
    and displaying the results from each search.

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
    python test_field_search_now.py

NOTES:
    - Requires Bloomberg broker running on localhost:8000
    - Uses API_KEY from .env file
=============================================================================
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('API_KEY', 'Caeser00**')
headers = {"x-api-key": API_KEY}

# Test field search
tests = [
    "last price",
    "PX_LAST",
    "market cap",
    "P/E ratio",
    "dividend"
]

print("Testing field search endpoint...\n")

for query in tests:
    print(f"Searching for: '{query}'")
    r = requests.get(
        "http://localhost:8000/blp/fields/search",
        params={"query": query, "limit": 5},
        headers=headers,
        timeout=10
    )
    
    if r.status_code == 200:
        data = r.json()
        print(f"  Found {data['total_results']} results")
        if data['results']:
            for result in data['results'][:3]:
                print(f"    - {result['mnemonic']}: {result['description']}")
    else:
        print(f"  ERROR: {r.status_code}")
    print()



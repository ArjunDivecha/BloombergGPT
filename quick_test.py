"""Quick test - just checks if basics work"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('API_KEY', 'Caeser00**')
headers = {"x-api-key": API_KEY}

print("\n=== QUICK TEST ===\n")

# Test 1: Single ticker
print("Test 1: Single ticker (AAPL)...")
try:
    r = requests.get(
        "http://localhost:8000/blp/refdata",
        params={"ticker": "AAPL", "fields": ["PX_LAST", "PE_RATIO", "CUR_MKT_CAP"]},
        headers=headers,
        timeout=10
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Data: {data.get('data', {})}")
        print("✓ WORKS")
    else:
        print(f"✗ FAILED: {r.text[:200]}")
except Exception as e:
    print(f"✗ ERROR: {e}")

# Test 2: Batch
print("\nTest 2: Batch (AAPL, MSFT, GOOGL)...")
try:
    r = requests.get(
        "http://localhost:8000/blp/refdata?ticker=AAPL&ticker=MSFT&ticker=GOOGL&fields=PX_LAST&fields=PE_RATIO",
        headers=headers,
        timeout=10
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        is_batch = isinstance(data.get('data', {}), dict) and len(data.get('data', {})) > 1
        print(f"Batch mode: {is_batch}")
        print(f"Tickers returned: {len(data.get('data', {})) if is_batch else 1}")
        print("✓ WORKS" if is_batch else "⚠ Single mode only")
    else:
        print(f"✗ FAILED: {r.text[:200]}")
except Exception as e:
    print(f"✗ ERROR: {e}")

print("\n=== END ===\n")


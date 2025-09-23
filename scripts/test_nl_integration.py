"""
Test Script for Natural Language Query Integration

INPUT FILES:
- None

OUTPUT FILES:
- Test Results: logs/nl_integration_test_results.txt

VERSION HISTORY:
- Date: September 22, 2025
- Author: AI Assistant
- Changes: Initial creation to test Phase 3 integration
"""

import requests
import json

BROKER_URL = "http://localhost:8000"
API_KEY = "Caeser00**"

def test_nl_query(query):
    """Test a natural language query"""
    headers = {"x-api-key": API_KEY}
    params = {"query": query}

    try:
        response = requests.get(f"{BROKER_URL}/blp/nlquery", params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# Test queries
test_queries = [
    "What's Apple's last price?",
    "What is the market cap for Microsoft?",
    "Show me Apple's volume",
    "Apple stock price"
]

results = []
for query in test_queries:
    result = test_nl_query(query)
    results.append({"query": query, "result": result})

# Save results
with open("logs/nl_integration_test_results.txt", "w") as f:
    f.write(json.dumps(results, indent=2))

print("Test results saved to logs/nl_integration_test_results.txt")
print("Sample result:")
print(json.dumps(results[0], indent=2))

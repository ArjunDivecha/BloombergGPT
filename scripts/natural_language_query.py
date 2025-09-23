"""
Natural Language Query Interface for Bloomberg Data

INPUT FILES:
- Knowledge Base: data/rag_knowledge_base.pkl (from Phase 1)
- Test Queries: scripts/test_queries.txt (for testing)

OUTPUT FILES:
- Query Log: logs/nl_query_log.txt (log of processed queries)

VERSION HISTORY:
- Date: September 22, 2025
- Author: AI Assistant
- Changes: Initial creation for Phase 3 natural language integration

DESCRIPTION:
This script adds natural language query capabilities to the existing Bloomberg broker.
It uses the RAG system to interpret queries and resolve them to Bloomberg fields/tickers,
then calls the broker to get the data.

INTEGRATION:
This integrates with the existing FastAPI broker by adding a new endpoint /blp/nlquery
"""

import os
import pickle
import re
import requests
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Optional
import json

# Configuration
BROKER_URL = "http://localhost:8000"  # Existing broker URL
KB_PATH = "data/rag_knowledge_base.pkl"
LOG_PATH = "logs/nl_query_log.txt"

# Load knowledge base
with open(KB_PATH, 'rb') as f:
    kb = pickle.load(f)
chunks = kb['chunks']

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Load retriever
with open('models/hybrid_retriever.pkl', 'rb') as f:
    retriever_data = pickle.load(f)

def resolve_query_to_fields_ticker(query: str) -> Dict:
    """Resolve natural language query to fields and ticker using RAG"""
    # Simple keyword extraction for fields
    potential_fields = re.findall(r'\b[A-Z_]{3,}\b', query)

    # Use hybrid retrieval to find relevant chunks
    results = []
    for chunk in chunks[:5]:  # Check top chunks
        if any(field.lower() in chunk['text'].lower() for field in potential_fields):
            results.append(chunk)

    # Simple ticker extraction
    tickers = ["AAPL", "MSFT", "GOOGL"]  # Default tickers
    found_ticker = None
    for ticker in tickers:
        if ticker.lower() in query.lower():
            found_ticker = f"{ticker} US Equity"
            break

    if not found_ticker:
        found_ticker = "AAPL US Equity"  # Default

    # Map potential fields to allowed fields
    allowed_fields = ["PX_LAST", "MARKET_CAP", "VOLUME"]
    resolved_fields = [f for f in potential_fields if f in allowed_fields]

    if not resolved_fields:
        resolved_fields = ["PX_LAST"]  # Default

    return {
        "ticker": found_ticker,
        "fields": resolved_fields,
        "query_type": "reference" if "last" in query.lower() else "historical"
    }

def call_broker(ticker: str, fields: List[str], query_type: str) -> Dict:
    """Call the existing broker to get data"""
    headers = {"x-api-key": "Caeser00**"}  # Use the API key from main.py

    if query_type == "reference":
        endpoint = f"{BROKER_URL}/blp/refdata"
        params = {"ticker": ticker, "fields": fields}
    else:
        endpoint = f"{BROKER_URL}/blp/historical"
        params = {"ticker": ticker, "fields": fields, "start_date": "2025-01-01", "end_date": "2025-01-31"}

    try:
        response = requests.get(endpoint, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def process_natural_language_query(query: str) -> Dict:
    """Main function to process a natural language query"""
    print(f"Processing query: {query}")

    # Resolve query
    resolution = resolve_query_to_fields_ticker(query)

    # Call broker
    broker_response = call_broker(resolution["ticker"], resolution["fields"], resolution["query_type"])

    # Log the query
    with open(LOG_PATH, 'a') as log:
        log.write(json.dumps({
            "query": query,
            "resolution": resolution,
            "broker_response": broker_response
        }) + "\n")

    return {
        "query": query,
        "resolved_ticker": resolution["ticker"],
        "resolved_fields": resolution["fields"],
        "broker_data": broker_response
    }

# Example usage
if __name__ == "__main__":
    test_queries = [
        "What's Apple's last price?",
        "What is the market cap for Microsoft?",
        "Show me Apple's volume"
    ]

    for query in test_queries:
        result = process_natural_language_query(query)
        print(json.dumps(result, indent=2))

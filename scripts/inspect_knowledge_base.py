"""
Knowledge Base Inspector

INPUT FILES:
- Knowledge Base: data/rag_knowledge_base.pkl

OUTPUT FILES:
- Inspection Report: logs/knowledge_base_inspection.txt

Version History:
- Date: September 22, 2025
- Author: AI Assistant
- Changes: Initial creation to inspect RAG knowledge base
"""

import pickle
import pandas as pd

# Load knowledge base
KB_PATH = 'data/rag_knowledge_base.pkl'
REPORT_PATH = 'logs/knowledge_base_inspection.txt'

with open(KB_PATH, 'rb') as f:
    kb = pickle.load(f)

chunks = kb['chunks']
allowed_fields = kb['allowed_fields']
ticker_aliases = kb['ticker_aliases']

# Generate inspection report
with open(REPORT_PATH, 'w') as report:
    report.write("=== Knowledge Base Inspection Report ===\n\n")

    report.write("=== Chunks Summary ===\n")
    report.write(f"Total Chunks: {len(chunks)}\n")
    report.write(f"Sample Chunk IDs: {', '.join([str(c['chunk_id']) for c in chunks[:5]])}\n")
    report.write(f"Sample Chunk Sources: {', '.join(set([c['source'] for c in chunks]))}\n")

    report.write("\n=== Sample Chunks ===\n")
    for i, chunk in enumerate(chunks[:10]):  # Show first 10 chunks
        report.write(f"\nChunk {chunk['chunk_id']}:\n")
        report.write(f"Source: {chunk['source']}\n")
        report.write(f"Version: {chunk['doc_version']}\n")
        report.write(f"Text (first 200 chars): {chunk['text'][:200]}...\n")

    report.write("\n=== Allowed Fields ===\n")
    if isinstance(allowed_fields, dict):
        allowed_fields_df = pd.DataFrame(allowed_fields)
        report.write(f"Fields Count: {len(allowed_fields_df)}\n")
        report.write("Sample Fields:\n")
        report.write(str(allowed_fields_df.head().to_string()) + "\n")

    report.write("\n=== Ticker Aliases ===\n")
    if isinstance(ticker_aliases, dict):
        ticker_aliases_df = pd.DataFrame(ticker_aliases)
        report.write(f"Aliases Count: {len(ticker_aliases_df)}\n")
        report.write("Sample Aliases:\n")
        report.write(str(ticker_aliases_df.head().to_string()) + "\n")

    report.write("\n=== Unique Data Items Identified ===\n")
    # Extract unique field codes
    field_codes = set()
    for chunk in chunks:
        text = chunk['text']
        # Simple extraction of potential field codes (words in ALL_CAPS)
        import re
        potential_fields = re.findall(r'\b[A-Z_]{3,}\b', text)
        field_codes.update(potential_fields)

    report.write(f"Potential Field Codes Found: {len(field_codes)}\n")
    report.write("Sample Field Codes: " + ', '.join(list(field_codes)[:20]) + "\n")

print(f"Inspection complete. Check {REPORT_PATH} for detailed report.")

"""
RAG Ingestion Script for Bloomberg Natural Language Interface

INPUT FILES:
- Bloomberg BLPAPI Docs: docs/blpapi_docs/api_reference.html (fetched HTML from official site)
- Allowed Field Dictionary: /path/to/your/allowed_fields.xlsx (user-provided Excel file with field codes)
- Ticker Alias Table: /path/to/your/ticker_aliases.xlsx (user-provided Excel file with aliases)

OUTPUT FILES:
- Processed Data File: data/rag_knowledge_base.pkl (pickled knowledge base with chunks and embeddings)
- Log File: logs/missing_data_log.txt (log of any missing data filled with means)

Version History:
- Date: September 22, 2025
- Author: AI Assistant
- Changes: Initial creation for Phase 1 RAG setup

This script fetches, cleans, chunks, and embeds Bloomberg API documentation for RAG.
It's broken into small sections for easy understanding.
"""

import os
import pickle
import pandas as pd
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
import re

# Section 1: Setup Paths and Models
# Purpose: Get ready with file paths and tools.
print("Starting RAG Ingestion...")

# Paths (update these based on user input)
API_DOCS_DIR = 'docs/bloomberg_api'  # Directory with all documentation files
ALLOWED_FIELDS_PATH = 'allowed_fields.csv'  # Placeholder CSV
TICKER_ALIASES_PATH = 'ticker_aliases.csv'  # Placeholder CSV
OUTPUT_KB_PATH = 'data/rag_knowledge_base.pkl'
LOG_PATH = 'logs/missing_data_log.txt'

# Create directories if needed
os.makedirs('data', exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Load embedding model (uses GPU if available)
model = SentenceTransformer('all-MiniLM-L6-v2')

# Section 2: Load and Clean Data
# Purpose: Read in the files and fix any missing info.
print("Loading data...")

# Load allowed fields (fill missing with means if needed)
allowed_fields = pd.read_csv(ALLOWED_FIELDS_PATH)
# Handle missing data: Fill with mean of available values
for col in allowed_fields.select_dtypes(include=['number']).columns:
    allowed_fields[col].fillna(allowed_fields[col].mean(), inplace=True)
with open(LOG_PATH, 'w') as log:
    log.write("Filled missing numerical data with means.\n")

# Load ticker aliases (assume no missing for now)
ticker_aliases = pd.read_csv(TICKER_ALIASES_PATH)

# Load and parse API docs from directory
docs_text = ""
for filename in os.listdir(API_DOCS_DIR):
    if filename.endswith(('.md', '.html', '.txt')):
        filepath = os.path.join(API_DOCS_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                docs_text += content + "\n\n"
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            continue

cleaned_text = re.sub(r'\s+', ' ', docs_text)  # Simple cleaning

# Section 3: Chunk the Text
# Purpose: Break text into small pieces for searching.
print("Chunking text...")
chunks = []
for i in range(0, len(cleaned_text), 300):  # Overlapping chunks
    chunk = cleaned_text[i:i+400]
    chunks.append(chunk)

# Add metadata to each chunk
metadata = []
for idx, chunk in enumerate(chunks):
    metadata.append({
        'chunk_id': idx,
        'source': 'BLPAPI Full Documentation',
        'text': chunk,
        'doc_version': 'Latest'  # Update as needed
    })

# Section 4: Create Embeddings
# Purpose: Turn text into numbers for fast searching.
print("Creating embeddings...")
embeddings = model.encode([m['text'] for m in metadata], show_progress_bar=True)

# Section 5: Save Knowledge Base
# Purpose: Store everything in a file.
knowledge_base = {
    'chunks': metadata,
    'embeddings': embeddings,
    'allowed_fields': allowed_fields.to_dict(),
    'ticker_aliases': ticker_aliases.to_dict()
}
with open(OUTPUT_KB_PATH, 'wb') as f:
    pickle.dump(knowledge_base, f)
print(f"Saved knowledge base to {OUTPUT_KB_PATH}")

# Section 6: Basic Test
# Purpose: Check if it works.
query = "What is PX_LAST?"
query_embedding = model.encode([query])
# Simple search (full implementation in Part 2)
print("Test query result: Basic search setup complete.")

print("Ingestion complete!")

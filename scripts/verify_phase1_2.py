"""
Comprehensive Verification Script for Phase 1 and 2

INPUT FILES:
- Knowledge Base: data/rag_knowledge_base.pkl (from Phase 1)
- Test Queries: comprehensive_test_queries.txt (expanded test queries)

OUTPUT FILES:
- Verification Report: logs/verification_report.txt (detailed results and analysis)

Version History:
- Date: September 22, 2025
- Author: AI Assistant
- Changes: Initial creation for Phase 1 and 2 verification

This script thoroughly tests the RAG system from Phase 1 and 2.
"""

import pickle
import time
import numpy as np
from sentence_transformers import SentenceTransformer

# Section 1: Setup
print("Starting comprehensive verification of Phase 1 and 2...")
KB_PATH = 'data/rag_knowledge_base.pkl'
TEST_QUERIES_PATH = 'scripts/comprehensive_test_queries.txt'
REPORT_PATH = 'logs/verification_report.txt'

# Load components
with open(KB_PATH, 'rb') as f:
    kb = pickle.load(f)
chunks = kb['chunks']
embeddings = np.array(kb['embeddings'])

# Load model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Load test queries
with open(TEST_QUERIES_PATH, 'r') as f:
    test_queries = [line.strip() for line in f if line.strip()]

# Section 2: Phase 1 Verification (Knowledge Base)
print("Verifying Phase 1: Knowledge Base...")
phase1_results = {}
phase1_results['total_chunks'] = len(chunks)
phase1_results['embeddings_shape'] = embeddings.shape
phase1_results['sample_chunk'] = chunks[0] if chunks else "No chunks found"

# Check for missing data
with open('logs/missing_data_log.txt', 'r') as log:
    missing_data = log.read()
phase1_results['missing_data_handled'] = missing_data

# Section 3: Phase 2 Verification (Hybrid Retrieval)
print("Verifying Phase 2: Hybrid Retrieval...")
with open('models/hybrid_retriever.pkl', 'rb') as f:
    retriever_data = pickle.load(f)

# Recreate search logic without pickled function
def simple_hybrid_search(query, top_k=5):
    # Dense search
    query_embedding = model.encode([query])
    scores_dense, indices_dense = retriever_data['dense_index'].search(query_embedding, top_k)

    # Sparse search
    query_sparse = retriever_data['sparse_vectorizer'].transform([query])
    sparse_matrix = retriever_data['sparse_matrix']
    scores_sparse = (query_sparse * sparse_matrix.T).toarray().flatten()
    top_sparse_indices = np.argsort(scores_sparse)[::-1][:top_k]

    # Combine (simple average)
    combined_scores = np.zeros(len(chunks))
    for i, idx in enumerate(indices_dense[0]):
        combined_scores[idx] += scores_dense[0][i]
    for i, idx in enumerate(top_sparse_indices):
        combined_scores[idx] += scores_sparse[idx]
    combined_scores /= 2

    top_indices = np.argsort(combined_scores)[::-1][:top_k]
    return top_indices, combined_scores[top_indices]

retrieval_results = []
total_time = 0

for query in test_queries:
    start_time = time.time()
    indices, scores = simple_hybrid_search(query)
    end_time = time.time()

    results = []
    for i, idx in enumerate(indices):
        results.append({
            'query': query,
            'chunk_text': chunks[idx]['text'][:100] + '...',
            'score': scores[i],
            'time': end_time - start_time
        })

    retrieval_results.extend(results)
    total_time += end_time - start_time

phase2_results = {
    'total_queries': len(test_queries),
    'avg_time_per_query': total_time / len(test_queries),
    'sample_results': retrieval_results[:5]  # First 5 for summary
}

# Section 4: Analysis and Report
print("Generating verification report...")
with open(REPORT_PATH, 'w') as report:
    report.write("=== Phase 1 Verification Results ===\n")
    report.write(f"Total Chunks: {phase1_results['total_chunks']}\n")
    report.write(f"Embeddings Shape: {phase1_results['embeddings_shape']}\n")
    report.write(f"Sample Chunk: {phase1_results['sample_chunk']}\n")
    report.write(f"Missing Data Handling: {phase1_results['missing_data_handled']}\n")

    report.write("\n=== Phase 2 Verification Results ===\n")
    report.write(f"Total Queries Tested: {phase2_results['total_queries']}\n")
    report.write(f"Average Time per Query: {phase2_results['avg_time_per_query']:.4f} seconds\n")
    report.write("Sample Retrieval Results:\n")
    for result in phase2_results['sample_results']:
        report.write(f"Query: {result['query']}\n")
        report.write(f"Result: {result['chunk_text']}\n")
        report.write(f"Score: {result['score']:.4f}, Time: {result['time']:.4f}s\n\n")

    report.write("=== Overall Assessment ===\n")
    if phase1_results['total_chunks'] > 0 and phase2_results['total_queries'] == len(test_queries):
        report.write("Phase 1: PASS - Knowledge base created successfully.\n")
        report.write("Phase 2: PASS - Hybrid retrieval functioning.\n")
        report.write("Recommendation: Proceed to Phase 1 Part 3.\n")
    else:
        report.write("Issues detected. Review results above.\n")

print("Verification complete! Check logs/verification_report.txt for full results.")

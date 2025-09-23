"""
Hybrid Retrieval System for Bloomberg Natural Language Interface

INPUT FILES:
- Knowledge Base: data/rag_knowledge_base.pkl (from Part 1, with chunks and embeddings)
- Test Queries: /path/to/your/test_queries.txt (user-provided file with sample questions)

OUTPUT FILES:
- Retrieval Model: models/hybrid_retriever.pkl (saved hybrid search model)
- Test Results: logs/retrieval_test_results.txt (results of test searches)

Version History:
- Date: September 22, 2025
- Author: AI Assistant
- Changes: Initial creation for Phase 1 Part 2

This script sets up hybrid retrieval (dense + sparse) for the RAG system.
"""

import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import faiss

# Section 1: Setup
print("Setting up Hybrid Retrieval...")
KB_PATH = 'data/rag_knowledge_base.pkl'
MODEL_PATH = 'models/hybrid_retriever.pkl'
TEST_QUERIES_PATH = 'scripts/test_queries.txt'  # Local test file
RESULTS_PATH = 'logs/retrieval_test_results.txt'

# Load knowledge base
with open(KB_PATH, 'rb') as f:
    kb = pickle.load(f)
chunks = kb['chunks']
embeddings = np.array(kb['embeddings'])

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Section 2: Dense Retrieval (FAISS)
print("Building dense index...")
dimension = embeddings.shape[1]
index = faiss.IndexFlatIP(dimension)  # Inner product for cosine
faiss.normalize_L2(embeddings)
index.add(embeddings)

# Section 3: Sparse Retrieval (TF-IDF)
print("Building sparse index...")
texts = [chunk['text'] for chunk in chunks]
vectorizer = TfidfVectorizer()
sparse_matrix = vectorizer.fit_transform(texts)

# Section 4: Hybrid Search Function
def hybrid_search(query, top_k=5, alpha=0.5):
    # Dense search
    query_embedding = model.encode([query])
    faiss.normalize_L2(query_embedding)
    scores_dense, indices_dense = index.search(query_embedding, top_k)

    # Sparse search (get top_k scores)
    query_sparse = vectorizer.transform([query])
    scores_sparse = cosine_similarity(query_sparse, sparse_matrix).flatten()
    top_sparse_indices = np.argsort(scores_sparse)[::-1][:top_k]
    scores_sparse_top = scores_sparse[top_sparse_indices]

    # Align scores to same indices
    combined_scores = np.zeros(len(chunks))
    for i, idx in enumerate(indices_dense[0]):
        combined_scores[idx] += alpha * scores_dense[0][i]
    for i, idx in enumerate(top_sparse_indices):
        combined_scores[idx] += (1 - alpha) * scores_sparse_top[i]

    top_indices = np.argsort(combined_scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        results.append({
            'chunk': chunks[idx],
            'score': combined_scores[idx]
        })
    return results

# Section 5: Save Model (data only, no function)
retriever = {
    'dense_index': index,
    'sparse_vectorizer': vectorizer,
    'sparse_matrix': sparse_matrix,
    'chunks': chunks
}
with open(MODEL_PATH, 'wb') as f:
    pickle.dump(retriever, f)
print(f"Saved retriever to {MODEL_PATH}")

# Section 6: Test
print("Testing retrieval...")
# Load test queries (user provides this file)
with open(TEST_QUERIES_PATH, 'r') as f:
    test_queries = f.read().splitlines()

with open(RESULTS_PATH, 'w') as log:
    for query in test_queries:
        results = hybrid_search(query)
        log.write(f"Query: {query}\nResults:\n")
        for res in results:
            log.write(f"  Score: {res['score']}, Text: {res['chunk']['text'][:100]}...\n")
        log.write("\n")

print("Hybrid retrieval setup complete!")

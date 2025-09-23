# README for Phase 1, Part 2: Implement Hybrid Retrieval System

**Purpose:**  
Now that we have the "library," we need a way to search it quickly—like a super-fast librarian who finds the exact book page for your question. This combines "dense" (smart word searches) and "sparse" (exact matches) to get accurate answers, as in PRD Section 5 (Embeddings & Indexing).

**Step-by-Step Instructions:**  
1. Load the knowledge base: Open the file we made in Part 1.  
2. Set up search tools: Create a system that turns questions into numbers (embeddings) for smart searching.  
3. Build the hybrid search: Mix dense (fuzzy matches) and sparse (exact word matches) to find the best info.  
4. Test searches: Try sample questions and see if it finds the right chunks.  
5. Save the search setup: Store it so we can use it in later parts.

**Input Files:**  
- Processed Data File: From Part 1 (rag_knowledge_base.pkl).  
- Sample Queries: A small file with test questions (e.g., "What is PX_LAST?"). Path: /path/to/your/test_queries.txt (you'll provide).

**Output Files:**  
- Retrieval Model File: A saved setup for searching (e.g., hybrid_retriever.pkl). Path: /Dropbox-1/AAA Backup/A Working/BloombergGPT/models/hybrid_retriever.pkl.  
- Test Results: A report on search accuracy. Path: /Dropbox-1/AAA Backup/A Working/BloombergGPT/logs/retrieval_test_results.txt.

**Dependencies:**  
- Python libraries: sentence-transformers (for embeddings), faiss (for fast searching).  
- Hardware: GPU on your Mac for quick embedding calculations.

**Notes:**  
- This maximizes your Mac's power for parallel searches.  
- Risk: If searches are too slow, we can tweak settings. We'll document any issues.

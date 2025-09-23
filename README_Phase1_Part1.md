# README for Phase 1, Part 1: Set Up RAG Knowledge Base (Ingestion and Processing)

**Purpose:**  
We need to collect and organize information from Bloomberg API documentation (like field codes and methods) so the system can understand user questions. This is like building a library from official guides. We'll fetch the docs, clean them, and make them searchable, following the PRD's rules for chunking and metadata.

**Step-by-Step Instructions:**  
1. Fetch the docs: Download the official BLPAPI Python documentation from Bloomberg's site (e.g., HTML pages or API reference).  
2. Parse and clean: Remove extra stuff like navigation menus, and organize into simple "cards" (small chunks for each field or method).  
3. Split into chunks: Break long sections into pieces (150–400 tokens each) so searches are fast and accurate.  
4. Add metadata: Tag each chunk with details like source, version, and field codes.  
5. Create embeddings: Turn text into numbers for smart searching.  
6. Save and test: Store everything and check with a few sample searches.

**Input Files:**  
- Bloomberg BLPAPI Docs: Official documentation (fetched from https://www.bloomberg.com/professional/support/api-library/ or similar; I'll provide the exact URL). Path: Downloaded to /Dropbox-1/AAA Backup/A Working/BloombergGPT/docs/blpapi_docs/ (folder created during fetch).  
- Allowed Field Dictionary: Your file with approved fields. Path: /path/to/your/allowed_fields.xlsx.  
- Ticker Alias Table: Your file with aliases. Path: /path/to/your/ticker_aliases.xlsx.

**Output Files:**  
- Processed Data File: A file with cleaned, chunked docs (e.g., rag_knowledge_base.pkl). Path: /Dropbox-1/AAA Backup/A Working/BloombergGPT/data/rag_knowledge_base.pkl.  
- Log File: A report on cleaning (e.g., missing_data_log.txt). Path: /Dropbox-1/AAA Backup/A Working/BloombergGPT/logs/missing_data_log.txt.  
- Version History: Updated with date and changes.

**Dependencies:**  
- Python libraries: requests or beautifulsoup4 (for fetching docs), pandas (for data), sentence-transformers (for embeddings).  
- Tools: Use `curl` or `wget` to download docs.

**Notes:**  
- If docs are missing or outdated, I'll note it and suggest updates.  
- This maximizes your Mac's GPU for processing.  
- Risk: Docs might change; we'll check for updates later.

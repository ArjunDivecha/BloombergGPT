 # Bloomberg Natural Language Interface — Full PRD (RAG + Semantic Chunking, Hybrid Retrieval, Compliance)

## 0) Purpose & Vision

Transform your existing Bloomberg Desktop API broker into a conversational, **retrieval-grounded** financial data platform. Users ask plain-English questions; the system resolves intent, maps to **approved Bloomberg fields and canonical tickers**, executes via your broker, and returns answers with **traceable provenance**.
This PRD incorporates: **semantic chunking**, **hybrid retrieval (dense+sparse)**, **ticker/field resolution**, **explainability**, and **compliance-first execution**.

---

## 1) Objectives & Success Criteria

**Primary objectives**

* **Accuracy:** Map user phrasing to the correct **fields**, **tickers**, **endpoints**, and **parameters** reliably.
* **Compliance:** Enforce allowed fields and entitlements before any data call; always return provenance.
* **Latency:** p95 < 3s for simple single-ticker snapshot queries (warm cache); < 6s for multi-ticker/historical.
* **Maintainability:** Refresh documentation and field dictionaries without redeploy; versioned indices.

**Key success metrics**

* Field mapping accuracy ≥ 95% on a curated gold set.
* Ticker normalization accuracy ≥ 98% (listed equities), ≥ 95% (indices/FX).
* Citation coverage ≥ 90% of answers (at least one authoritative source per response).
* Disallowed-field blocks = 100% (with suggested allowed alternatives).
* User helpfulness ≥ 4.2/5 in pilot surveys.
* p95 latency targets met for each supported query family.

---

## 2) Scope

**In scope (Phase 1)**

* Reference snapshots (e.g., last price, volume) and historical windows.
* Simple multi-ticker comparisons and basic derived metrics (e.g., % change vs prior close).
* RAG over public BLPAPI docs plus internal **Allowed Field Dictionary** and curated **Ticker Alias Table**.
* Explanations, citations, and a machine-readable “validated request” echo for every answer.

**Out of scope (Phase 1)**

* Real-time streaming UI (subscriptions).
* Portfolio analytics, factor models, or proprietary datasets beyond the Desktop API.
* Server-side chart rendering (system returns structured series; client can chart).

---

## 3) Personas & Core Use Cases

**Personas**

* **Analyst/PM:** Needs quick answers without remembering field codes or ticker formats.
* **Trader:** Fast comparative snapshots and short historical stats.
* **Data Engineer:** Field discovery, parameter correctness, and diagnostics.
* **Support/QA:** Auditability; why a query failed and how it was resolved.

**Representative queries**

* “What’s Apple’s last price and % change vs yesterday close?”
* “Compare MSFT and AAPL 1-month return.”
* “Which field gives dividend ex-date for MSFT?”
* “Why did my request fail?” (expect plan + validation path + broker error, if any)

---

## 4) System Overview (Four Layers; RAG inside Translation)

1. **Natural Language Layer**
   Intent detection, entity extraction (tickers, dates, metrics), constraint parsing (asset class limits, max tickers).

2. **Query Translation Layer (RAG-powered)**
   Semantic retrieval over a **semantic-chunked** doc index; field discovery; ticker normalization; compliance checks; query planning (ref vs hist, parameters); execution plan; explainability artifacts.

3. **Existing Bloomberg Broker (FastAPI)**
   Authentication, rate limiting, allowed-fields enforcement, entitlements, auditing, structured errors.

4. **Bloomberg Desktop API**
   Reference data, historical data, and allowed discovery endpoints.

**Design note:** RAG is a **subsystem** of the Translation Layer; no fifth layer is introduced.

---

## 5) Knowledge Sources & Ingestion (RAG)

**Sources**

* Public BLPAPI Python documentation (versioned).
* Internal **Allowed Field Dictionary** (authoritative execution policy).
* Internal FAQs/how-tos you own (optional, non-licensed).
* **Ticker Alias Table** (curated, non-proprietary).

**Parsing & cleaning**

* Convert HTML to clean Markdown/text; strip navigation/boilerplate.
* Preserve headings (H2/H3), anchor IDs, code identifiers (e.g., `PX_LAST`, `DVD_EX_DT`), and method signatures.
* Normalize tables; **flatten field tables into row-level “field cards.”**

**Semantic chunking**

* **Entity-scoped chunks (primary):** one chunk per **field**, **class**, **method**, **exception**. Target 150–400 tokens; do not mix multiple entities.
* **Narrative chunks (secondary):** long guides split by H2/H3 and then semantically at \~300–500 tokens with 10–15% overlap.
* **Sliding-window backup (optional):** small overlapping windows (\~300–400 tokens) only for narrative pages to catch variant phrasings.

**Metadata (attach to every chunk)**

* `source_url`, `doc_version`, `doc_type` (api\_ref, howto, faq), `section_path` (e.g., Class > Method), `entity_type` (field/class/method/exception), `canonical_id` (e.g., `PX_LAST`), `asset_classes`, `aliases` (e.g., “last price”), `hash`, `ingested_at`.
* **Anchor strings** for sparse retrieval: exact tokens like `PX_LAST`, `AAPL US Equity`, `USGG10YR Index`, `EURUSD Curncy`.

**Embeddings & indexing**

* Single modern text embedding family (consistent across splitting heuristics and retrieval).
* **Hybrid retrieval:** dense vectors + sparse keyword/BM25 over anchors; exact code tokens get strong boosts.
* **Re-ranking (Phase 2):** lightweight cross-encoder or LLM re-ranker over the top-k.
* Deduplicate top-k by URL/section; recommended k = 6–10.

**Versioning & refresh**

* Include `doc_version` in metadata; default to latest; allow explicit version filters.
* Nightly or on-demand incremental reindex; surface index version and source hashes in `/health`.

---

## 6) Query Handling (end-to-end)

**6.1 Intent & entities**

* Detect query family: reference, historical, comparative, field-lookup, diagnostics.
* Extract entities: tickers (free text), dates/durations (“yesterday”, “1m”), metrics (“% change”, “dividend ex-date”), and constraints.

**6.2 RAG retrieval**

* Map user phrases to **field cards** (e.g., “last price” → `PX_LAST`; “dividend ex-date” → `DVD_EX_DT`).
* Retrieve method/parameter chunks if needed (e.g., how to specify periodicity).
* Retrieve alias rules for ticker formats and asset classes.

**6.3 Ticker normalization**

* Resolve aliases to canonical forms (e.g., “Apple” → `AAPL US Equity`; FX “EURUSD Curncy\`; UST index formats).
* If ambiguous: return top N candidates with confidence scores and require confirmation when below threshold.

**6.4 Compliance gate (authoritative)**

* Intersect requested fields with **Allowed Field Dictionary**; hard-block disallowed fields and suggest the nearest allowed alternatives with rationale.
* Enforce asset-class constraints and parameter bounds (e.g., max tickers, date limits).

**6.5 Query planning**

* Choose endpoint (ref vs hist), periodicity, adjustments (if applicable), date windows, fan-out strategy for multi-ticker.
* Apply concurrency and rate-limit budgets derived from the broker’s policies.

**6.6 Execution & synthesis**

* Execute via the broker; capture provenance and errors.
* Synthesize response: concise answer first, then key numbers/series, then a short explanation of calculations/assumptions.
* Always return **citations** and a machine-readable **validated\_request** echo.

---

## 7) External Interfaces (contracts, not code)

**7.1 Natural Language Query — POST /blp/query**

* **Inputs**

  * `query`: user’s question (string).
  * `constraints` (optional): asset class, max tickers, date bounds, version preference.
  * `mode` (optional): `explain` flag to include detailed plan/provenance.
* **Outputs**

  * `answer`: concise text.
  * `data`: structured payload (e.g., values, time series with timestamps and units).
  * `citations`: array of {title, url, section, doc\_version}.
  * `validated_request`: {endpoint, tickers\[], fields\[], params{…}} exactly as executed.
  * `notes`: warnings, assumptions, substitutions, disambiguation outcomes.
  * `errors`: typed errors (see taxonomy).

**7.2 Plan/Introspection — POST /blp/query/plan**

* Returns the planning artifacts only: intent, extracted entities, selected fields/tickers (with confidence), compliance outcomes, retrieval hits (ids and metadata), broker request(s) to be executed.

**7.3 Admin**

* **POST /rag/reindex:** Trigger incremental reindex; returns new index/version info.
* **PUT /config/allowed-fields:** Upsert allowed/dissallowed fields and aliases (admin-auth).
* **GET /health:** Liveness/readiness; index version(s), doc counts, last ingest timestamps.

---

## 8) Policies & Guardrails

* **Allowed Field Dictionary is authoritative.** If a requested field isn’t allowed, the call is blocked and the user is shown near-matches with reasoning.
* **Citations are mandatory** whenever field discovery or mapping occurs; responses without any citation are suppressed or downgraded (internal alert).
* **Explainability by default:** Always include `validated_request` with canonical tickers, fields, endpoint, and parameters.
* **Disambiguation flow** is required when ticker confidence is below threshold or multiple asset classes conflict.
* **Rate limits:** NL endpoint has stricter limits than raw broker calls; surge control is in the Translation Layer (pre-execution).

---

## 9) Non-Functional Requirements

**Performance**

* p95 latency: < 3s simple; < 6s comparative/historical on warm caches.
* Concurrency and back-pressure controls to protect the broker and Desktop API.

**Reliability**

* Graceful degradation: if RAG is unavailable, serve top “template” intents that rely on pre-approved fields (e.g., `PX_LAST`) with an explicit banner indicating reduced grounding.

**Security & Licensing**

* Authenticate all endpoints; encrypt in transit and at rest.
* Log only non-sensitive metadata; apply redaction where needed.
* Index only public docs and your own content; do not store licensed Terminal content beyond permitted use.
* Enforce data retention and deletion policies.

**Maintainability**

* Configuration-driven (Allowed Field Dictionary, Ticker Alias Table, RAG Source Catalog).
* Hot-reload or admin APIs for updates without redeploy.

---

## 10) Observability

**Structured logs**

* Request id, user id (hash), intent, selected fields/tickers, index version, latency breakdown by stage (NL, RAG, broker), compliance decisions, error codes.

**Metrics**

* Online field-mapping accuracy (via sampled human review).
* Retrieval hit rate and Recall\@k for correct entity chunk (using a rotating gold set).
* Citation presence rate, disallowed-field block rate.
* Correction/escalation rate, ambiguous-ticker frequency.
* Latency p50/p95 and error rates per stage.

**Tracing**

* Distributed spans across layers; identify hotspots (e.g., RAG retrieval vs broker time).

---

## 11) Data & Config Artifacts

**Allowed Field Dictionary (authoritative)**

* Fields: `field_code`, `human_label`, `description`, `endpoint_type` (ref/hist), `units`, `asset_classes[]`, `tags[]`, `aliases[]`, `status` (allowed/blocked), `closest_allowed[]`, `last_reviewed_at`.

**Ticker Alias Table**

* Fields: `alias`, `canonical_ticker`, `asset_class`, `confidence`, `region/currency` (if applicable), `notes`, `updated_at`.

**RAG Source Catalog**

* Fields: `doc_id`, `source_url`, `doc_version`, `doc_type` (api\_ref/howto/faq), `hash`, `status` (active/deprecated), `ingested_at`.

**Index Manifest**

* Fields: `index_id`, `embedding_model`, `build_time`, `doc_count`, `chunk_count`, `top_k_default`, `sparse_enabled` (bool), `reranker` (if any).

---

## 12) Error Taxonomy (examples)

* `INTENT_UNCLEAR`: multiple plausible intents; return top 3 interpretations and request clarification.
* `TICKER_AMBIGUOUS`: present disambiguation candidates with confidences.
* `FIELD_NOT_ALLOWED`: block; provide closest allowed fields and policy reason.
* `UNSUPPORTED_QUERY`: out of scope; suggest supported alternatives.
* `BROKER_ERROR`: include broker code/message and actionable next steps.
* `RAG_CITATION_MISSING`: internal only; answer downgraded or withheld.

---

## 13) UX & Answering Rules

* **Answer first**, then key numbers/series, then a one-to-two sentence explanation (calculations, assumptions), then citations (title + URL + version).
* Use consistent **units and rounding** (per-field rules in the dictionary).
* For historical series and comparisons, return a compact table/series structure plus a concise insight (e.g., “MSFT outperformed AAPL by 1.7% over 1M”).
* Always show the **validated request** object so users can reproduce calls directly.
* When assumptions are made (default periodicity, adjustments), state them.

---

## 14) Evaluation Plan

**Offline (pre-launch)**

* Gold set: 200–400 labeled queries covering all supported families, with special focus on field discovery and tricky tickers.
* Metrics: field mapping accuracy, ticker normalization accuracy, endpoint/parameter selection accuracy, Recall\@k for the correct entity chunk, citation validity.
* **Ablations:** semantic-only vs fixed windows vs hybrid; dense-only vs hybrid dense+sparse; with/without re-ranking.

**Online (pilot)**

* Human helpfulness ratings, correction rate, ambiguous-ticker prompts per 100 queries.
* Guardrail audits: random samples for citation correctness and allowed-field enforcement.
* Latency SLOs tracked per query family.

**Acceptance criteria**

* Meets accuracy thresholds (95% fields, 98% equity tickers, 90% citation coverage).
* Meets latency targets on warm cache.
* Disallowed-field enforcement at 100% with alternatives suggested.

---

## 15) Rollout Plan

**Phase 0 — Prototype (internal)**

* Build semantic-chunked index (entity-scoped field cards + class/method pages).
* Enable hybrid retrieval (dense + sparse anchors) with top-k dedupe.
* Implement single-ticker snapshot path with citations and validated\_request.
* Wire observability (logs/metrics/tracing).

**Phase 1 — MVP**

* Add historical windows and simple comparisons.
* Implement disambiguation flow for tickers; surface substitutions/assumptions.
* Admin endpoints for reindex and allowed-field updates.
* Pilot with a small user group; collect metrics and feedback.

**Phase 2 — Enhancements**

* Add re-ranking, query-suggestion hints, cached intent shortcuts.
* Expand asset-class coverage (rates, credit indices) and alias libraries.
* Introduce alert syntax parsing (policy-compliant, queued jobs) and richer diagnostics.

---

## 16) Risks & Mitigations

* **Hallucinated fields:** Require a positive hit in the Allowed Field Dictionary before execution; otherwise block and suggest matches.
* **Ticker ambiguity:** Mandatory disambiguation when confidence low; cache user selections.
* **Doc/version drift:** Nightly diffs; expose index version in `/health`; cite version in every answer.
* **Latency spikes:** Cache common intents and retrieval results; use a smaller intent model with escalation only when needed.
* **Over-chunking or boilerplate pollution:** Enforce entity-scoped chunks; strip nav/footers; monitor retrieval quality with Recall\@k.

---

## 17) Deliverables (what the implementation must produce)

* **RAG Ingestion Pipeline Design:** crawler, parser, semantic chunker spec, metadata schema, refresh strategy.
* **Retrieval Service Design:** dense+sparse retrieval policy, top-k, dedupe rules, optional re-ranker.
* **Query Translation Spec:** intent taxonomy, entity extraction schema, field/ticker resolution rules, compliance checks, planning logic.
* **External API Contracts:** `/blp/query`, `/blp/query/plan`, `/rag/reindex`, `/config/allowed-fields`, `/health` (field names, types, and error taxonomy).
* **Config Schemas:** Allowed Field Dictionary, Ticker Alias Table, RAG Source Catalog, Index Manifest.
* **Observability Spec:** required log fields, metrics, dashboards, alerts.
* **Evaluation Harness:** gold set framework, ablations, reporting; acceptance test suite.
* **Operational Runbook:** reindex process, rotating embeddings, adding sources, rollback.

---

## 18) Maintenance & Governance

* **Ownership:**

  * RAG ingestion + retrieval: Platform/Infra.
  * Allowed Field Dictionary: Data Governance (with compliance review).
  * Ticker Alias Table: Data Engineering (input from users; review cadence monthly).
* **Change control:**

  * PR-based updates to config repos; CI validates schemas; staging index before prod.
* **Review cadence:**

  * Monthly review of field dictionary and alias coverage; quarterly performance/accuracy audit.

---

### Final Note

This PRD is implementation-ready: it specifies **what** to build and the constraints under which it must operate (accuracy, latency, compliance, provenance). When you’re ready for implementation details, we can convert these contracts and schemas into code and tests—end-to-end—without deviating from the principles above.

# Repository Guidelines

## Project Structure & Module Organization
- `main_restricted.py` — FastAPI app (`app`) exposing Bloomberg broker endpoints.
- `requirements.txt` — runtime deps (install `blpapi` separately from Bloomberg).
- `Production Data/` — `Schema.yaml`, field catalog Excel.
- `scripts/` — utilities (e.g., `field_search_india.py`, `secf.py`).
- `archive/` — retired/legacy tooling.
- Tests — ad‑hoc scripts: `quick_test.py`, `test_field_service.py`, `test_account_capabilities.py`.
- Ops (Windows) — `start_bloomberg_broker.bat`, `stop_bloomberg_broker.bat`, `start_cloudflared.bat`, `check_status.py`.

## Build, Test, and Development Commands
- Setup
  - `python -m venv .venv && source .venv/bin/activate` (Win: `.\.venv\Scripts\activate`)
  - `pip install -r requirements.txt`
  - Install Bloomberg `blpapi` wheel manually: `pip install path/to/blpapi-<ver>.whl`
  - Copy env: `cp env.template .env` and set `API_KEY`, hosts/ports.
- Run locally
  - `python main_restricted.py` (or) `uvicorn main_restricted:app --reload --host 0.0.0.0 --port 8000`
  - Quick check: `curl -H "x-api-key: <key>" "http://localhost:8000/blp/fields?limit=1"`
- Tests (server running)
  - `python quick_test.py`
  - `python test_field_service.py`
  - `python test_account_capabilities.py`

## Coding Style & Naming Conventions
- Python, 4‑space indent, PEP 8; keep lines ≲100 chars.
- Names: `snake_case` for files/functions, `CamelCase` for classes, `UPPER_SNAKE` for constants.
- Prefer type hints, docstrings on public functions, and small focused helpers.
- Routes: follow existing patterns (`/blp/...`), return JSON with stable keys.
- Imports grouped stdlib/third‑party/local and alphabetized.

## Testing Guidelines
- No pytest suite; tests are runnable scripts. Start server, then run the test files above.
- Validate changed endpoints with `curl` and include sample responses in PRs.
- If `blpapi` is missing, mock paths return "No Data"; use for local dev only.

## Commit & Pull Request Guidelines
- Commits: imperative, present tense, concise summary (≤72 chars), optional body/bullets.
  - Examples: "Add BEQS endpoint", "Enhance field search filters".
- PRs: clear description, linked issues, steps to reproduce, before/after behavior, and test evidence.
- Required when changing APIs: update `openapi_spec.yaml` or `Production Data/Schema.yaml` and relevant docs.
- Do not commit secrets: `.env`, Cloudflare creds, API keys.

## Security & Configuration Tips
- `.env` controls `API_KEY`, `BROKER_HOST/PORT`, `BLOOMBERG_HOST/PORT`, `RATE_LIMIT`, `BROKER_DEBUG`.
- Bloomberg Terminal must be running for live data; otherwise mocks are returned.

## Bloomberg ASKB API Discovery
- For Bloomberg ASKB or "how do I access this Bloomberg data programmatically?" tasks, use the shared skill:
  `/Users/arjundivecha/.claude/skills/bloomberg-askb-api-discovery/SKILL.md`.
- If that global path is not mounted in the active Codex session, use the
  project-local fallback:
  `skills/bloomberg-askb-api-discovery/SKILL.md`.
- The deliverable is an API-access recipe, not Terminal navigation. Prefer BQL, BLPAPI, BDP, BDH, BDS, Bloomberg Excel, or BQuant instructions with exact securities, fields, overrides, date handling, and a minimal reproducible test.
- Use ASKB for discovery only. If ASKB gives only screens/functions, ask the API-access follow-up from the skill before stopping.
- Before asking ASKB, check whether the ASKB screen is already open and usable. If it is not open, prompt the user to open Bloomberg Terminal ASKB in the Windows VM and wait for confirmation.
- Validate ASKB output through the local broker, Bloomberg API, Bloomberg Excel, or BQuant before marking confidence high.
- Save reusable validated recipes in:
  `/Users/arjundivecha/Dropbox/AAA Backup/A Working/BloombergGPT/bloomberg_knowledge/field_dictionary.json`.
- Save concise ASKB session notes in:
  `/Users/arjundivecha/Dropbox/AAA Backup/A Working/BloombergGPT/bloomberg_knowledge/askb_sessions/`.
- Do not use computer use for order-entry, EMSX, FXGO, BUY/SELL screens, trade tickets, unattended sensitive workflows, or bulk GUI scraping.

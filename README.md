# Bloomberg Data Broker on Cloudflare Tunnel

This repository hosts a FastAPI "Bloomberg Data Broker" that brokers requests from ChatGPT (or any HTTP client) to the Bloomberg Desktop API. The project is wired for a permanent Cloudflare Tunnel URL so you no longer have to copy/paste temporary ngrok domains after every reboot.

## Features

- **10 Bloomberg API Endpoints**: Reference data, historical data, bulk data, field discovery, securities search, and equity screening
- **Dynamic Field Discovery**: Search Bloomberg's live 24,000+ field catalog by keyword
- **Bulk Data Service (BDS)**: Access 530+ bulk/tabular data fields (dividends, earnings, revenue, shareholders, etc.)
- **Bloomberg Equity Screening (BEQS)**: Run saved screens from Bloomberg Terminal
- **Security Search**: Find Bloomberg tickers and instruments (SECF-style)
- **Field Service**: Real-time field search, detailed metadata, and complete catalog browsing
- **API Key Authentication**: Secure access with x-api-key header
- **Rate Limiting**: 60 requests/minute per key
- **Cloudflare Tunnel**: Permanent HTTPS URL (no more ngrok copy/paste!)

The guide below walks through setting it up from scratch on a new Windows machine.

---

## 1. Prerequisites

| Requirement | Notes |
|-------------|-------|
| Bloomberg Terminal | Must be installed, logged in, and licensed for Desktop API access. |
| Python 3.8+ | Add to PATH during installation. |
| Cloudflare account + domain | Domain must be onboarded and pointing at Cloudflare nameservers. |
| `cloudflared.exe` | Data folder already contains the binary. |
| Git | Optional but recommended for cloning repo / pulling updates. |

---

## 2. Clone or copy the repository

```powershell
cd C:\path\to\workspace
git clone <repo-url> BloombergGPT
cd BloombergGPT
```

If you received the files another way, ensure everything sits under a single folder (e.g., `C:\BloombergGPT`).

---

## 3. Install Python dependencies

Use the helper script once. It installs packages, copies `.env`, and creates desktop shortcuts.

```powershell
setup_environment.bat
```

After it finishes:
- Edit `.env` if you need to change the default API key or Bloomberg host/port.
- Confirm the shortcuts �Start Bloomberg Broker� and �Stop Bloomberg Broker� were added to your desktop.

---

## 4. Configure the Cloudflare tunnel (one-time per machine)

1. **Log in `cloudflared`**
   ```powershell
   cloudflared.exe tunnel login
   ```
   Approve via browser; this drops a certificate in `%USERPROFILE%\.cloudflared`.

2. **Create the tunnel**
   ```powershell
   cloudflared.exe tunnel create bloomberg-broker
   ```
   Note the credentials JSON path printed (e.g., `C:\Users\you\.cloudflared\<uuid>.json`).

3. **Point DNS to the tunnel**
   ```powershell
   cloudflared.exe tunnel route dns bloomberg-broker broker.your-domain.com
   ```
   (Or edit a CNAME in the Cloudflare dashboard manually.)

4. **Create the tunnel config file**
   Save the snippet below as `C:\Users\you\Documents\cloudflared-broker.yml` (adjust paths as needed):
   ```yaml
   tunnel: bloomberg-broker
   credentials-file: C:\Users\you\.cloudflared\<uuid>.json
   ingress:
     - hostname: broker.your-domain.com
       service: http://localhost:8000
     - service: http_status:404
   ```

5. **Test run**
   ```powershell
   cloudflared.exe tunnel --config "C:\Users\you\Documents\cloudflared-broker.yml" run bloomberg-broker
   ```
   Hit `https://broker.your-domain.com/blp/fields?limit=1` with your API key header; you should see JSON (or a 401 if the key is wrong).

6. **Convenience batch file (optional)**
   Update `start_cloudflared.bat` if your config path differs. The file currently runs:
   ```bat
   @echo off
   pushd "\\mac\Dropbox-1\AAA Backup\A Working\BloombergGPT"
   cloudflared.exe tunnel --config "C:\Users\macbook2024\Documents\cloudflared-broker.yml" run bloomberg-broker
   popd
   ```
   Adjust paths to match your environment.

---

## 5. Starting the system each day

1. Launch the Bloomberg Terminal and sign in.
2. Double-click `Start Bloomberg Broker` (the desktop shortcut).
   - A broker window (Uvicorn) will start.
   - A tunnel window will start via `start_cloudflared.bat`.
   - A status window will open (`check_status.py`).
3. Confirm the status window reports everything as `[OK]`.
4. Update your ChatGPT Custom GPT (or any client) to use the permanent base URL `https://broker.your-domain.com`.

---

## 6. Stopping the system

- Double-click `Stop Bloomberg Broker`.
- This kills the Python broker and the Cloudflare tunnel and confirms port 8000 is free.

---

## 7. Repository layout (updated)

```
BloombergGPT/
+-- main.py                          # FastAPI broker (v2.2.0)
+-- GPT_System_Prompt_Adventurous.md # Adventurous system prompt for ChatGPT Custom GPT
+-- start_bloomberg_broker.bat       # Launch broker + Cloudflare tunnel + status
+-- stop_bloomberg_broker.bat        # Cleanup script
+-- start_cloudflared.bat            # Standalone tunnel runner
+-- check_status.py / check_status.bat
+-- env.template                     # Copy to .env and edit
+-- Production Data/
    +-- Schema.yaml                  # OpenAPI spec with 10 endpoints
    +-- Bloomberg Master Field List.xlsx  # Curated 3,674 fields
+-- Documentation/
    +-- FIELD_SERVICE_GUIDE.md       # Field discovery & search guide
    +-- BDS_FIELD_GUIDE.md           # 530+ bulk data fields reference
    +-- BEQS_SCREENING_GUIDE.md      # Equity screening guide
    +-- BDS_QUICK_REFERENCE.md       # Top bulk fields quick ref
+-- archive/                         # Legacy scripts (ngrok etc.)
+-- scripts/
    +-- field_search_india.py        # Standalone field search tool
+-- README_OPERATIONS.md             # Ops quick reference
```

---

## 8. Updating the API schema / GPT connector

- The schema file `Production Data/Schema.yaml` already points to the Cloudflare hostname:
  ```yaml
  servers:
    - url: https://broker.dancing-ganesh.com
      description: Bloomberg Data Broker via Cloudflare tunnel - UNRESTRICTED
  ```
- Paste this schema into your GPT�s Action or Tool config, or expose it via OpenAPI as needed.

---

## 9. Monitoring & troubleshooting

- Run `check_status.bat` to see health checks for environment, Bloomberg API, broker process, API endpoints, and Cloudflare tunnel.
- Tunnel window not running? Launch `start_cloudflared.bat` manually.
- Broker returning mock data? Ensure the Bloomberg Terminal is running and logged in; restart `start_bloomberg_broker.bat`.
- DNS not resolving? Check Cloudflare dashboard > DNS tab to confirm the CNAME points to `<tunnel-id>.cfargotunnel.com`.

---

## 10. Maintenance tips

- Keep `cloudflared.exe` updated (`cloudflared.exe update`).
- Rotate the API key in `.env` and in your GPT config if you share access.
- Pull latest repo changes periodically (`git pull`).
- Archive or delete the old ngrok tooling; it is no longer used.

---

## 11. Support / Logs

- Broker logs appear in the Uvicorn console window.
- Cloudflare logs appear in the tunnel window (or via `cloudflared service` if installed as a service).
- For a full reset: run `stop_bloomberg_broker.bat`, restart the Bloomberg Terminal, then run `start_bloomberg_broker.bat`.

---

## 12. Available Endpoints

The Bloomberg Data Broker provides 10 comprehensive endpoints:

### Data Retrieval
1. **`/blp/refdata`** - Current reference data (prices, fundamentals, company info)
2. **`/blp/historical`** - Historical time-series data with smart periodicity
3. **`/blp/bulkdata`** - Bulk/tabular data (530+ BDS fields)

### Field Discovery (NEW in v2.2.0)
4. **`/blp/fields/search`** - Search Bloomberg's 24,000+ fields by keyword
5. **`/blp/fields/info`** - Get detailed metadata for specific fields
6. **`/blp/fields/list`** - Browse complete field catalog by type (Static/RealTime)

### Utilities
7. **`/blp/fields`** - Static curated field list (3,674 fields)
8. **`/blp/coverage`** - Check Bloomberg coverage for a ticker
9. **`/blp/securities`** - Search for Bloomberg tickers (SECF-style)
10. **`/blp/screen`** - Run Bloomberg Equity Screens (BEQS)

### Documentation
- **`FIELD_SERVICE_GUIDE.md`** - Complete guide to field discovery endpoints
- **`BDS_FIELD_GUIDE.md`** - 530+ bulk data fields organized by category
- **`BEQS_SCREENING_GUIDE.md`** - Equity screening usage guide
- **`BDS_QUICK_REFERENCE.md`** - Quick reference for top 10 bulk fields

Happy data brokering!

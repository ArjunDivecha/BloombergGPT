# Bloomberg Data Broker – Operations Guide

## Quick Start

### One-Time Setup
1. Run `setup_environment.bat` to install dependencies and create shortcuts.
2. On Cloudflare, onboard your domain and create the tunnel configuration (`cloudflared-broker.yml`).

### Daily Use
1. Start the Bloomberg Terminal and log in.
2. Double-click `start_bloomberg_broker.bat` (launches the broker and Cloudflare tunnel).
3. Use your Bloomberg ChatGPT integration.

## Directory Overview
```
Bloomberg-Data-Broker/
+-- main.py                     # FastAPI Bloomberg broker
+-- requirements.txt            # Python dependencies
+-- start_bloomberg_broker.bat  # Start broker + Cloudflare tunnel + status
+-- stop_bloomberg_broker.bat   # Stop broker + Cloudflare tunnel
+-- start_cloudflared.bat       # Convenience wrapper for cloudflared
+-- check_status.py             # Console status dashboard
+-- env.template                # Copy to .env with your values
+-- README_OPERATIONS.md        # This guide
```

## Common Commands
| Action            | File / Command                | Description                          |
|-------------------|--------------------------------|--------------------------------------|
| Start system      | `start_bloomberg_broker.bat`   | Launch broker, tunnel, status window |
| Stop system       | `stop_bloomberg_broker.bat`    | Cleanly terminate all processes      |
| Check status      | `check_status.bat`             | Runs the Python status dashboard     |
| First-time setup  | `setup_environment.bat`        | Installs requirements, creates links |

## System Components
### 1. Bloomberg Data Broker
- Port: 8000
- Key endpoints: `/blp/fields`, `/blp/coverage`, `/blp/refdata`, `/blp/historical`

### 2. Cloudflare Tunnel (`cloudflared`)
- Purpose: Expose the local broker via `https://broker.your-domain.com`
- Config file: `cloudflared-broker.yml`
- Start: part of `start_bloomberg_broker.bat` or run manually with `start_cloudflared.bat`

### 3. Bloomberg Terminal
- Requirement: Terminal must be running and authenticated
- Bloomberg API port: 8194

## Health Checks
- Run `check_status.bat` for a live dashboard (verifies environment, Bloom-berg API, broker API, and Cloudflare tunnel).
- Manual quick test: `curl -H "x-api-key: <key>" http://localhost:8000/blp/fields?limit=1`

## Troubleshooting
| Problem                    | Solution                                      |
|---------------------------|-----------------------------------------------|
| Port 8000 in use          | Run `stop_bloomberg_broker.bat`                |
| Cloudflare tunnel missing | Launch `start_cloudflared.bat`                 |
| Bloomberg API error       | Ensure Terminal is running/logged in          |
| GPT can’t connect         | Confirm DNS points to Cloudflare tunnel URL   |

### Error Messages
- **"Failed to start Bloomberg session"** – confirm Terminal is running and logged in.
- **"Broker API not responding"** – check the Uvicorn window; restart the broker.
- **"Cloudflare tunnel not detected"** – run `start_cloudflared.bat` or install the tunnel as a Windows service.

## Daily Workflow
**Morning**
1. Launch Bloomberg Terminal.
2. Double-click `start_bloomberg_broker.bat`.
3. Verify `https://broker.your-domain.com/blp/fields?limit=1` returns JSON.
4. Use ChatGPT.

**Evening**
1. Double-click `stop_bloomberg_broker.bat`.
2. Optionally close Bloomberg Terminal.

## Security Notes
- Keep the API key secret; rotate if shared.
- Broker listens on localhost only; external access comes through the Cloudflare tunnel.
- Use HTTPS endpoints when configuring GPT.

## System Requirements
- Windows with Python 3.8+
- Bloomberg Terminal desktop session
- Internet connectivity for Cloudflare tunnel
- Ports 8000 (broker) and 8194 (Bloomberg API) available

## Support
- Broker logs: displayed in the Uvicorn console window
- Cloudflare logs: displayed in the tunnel window or via `cloudflared service` logs
- To reset everything: run `stop_bloomberg_broker.bat`, restart Bloomberg Terminal, then run `start_bloomberg_broker.bat`

## Success Indicators
- Bloomberg Terminal shows a live session.
- Broker window displays `Uvicorn running on http://0.0.0.0:8000`.
- Cloudflare window shows active connections for `broker.your-domain.com`.
- ChatGPT returns Bloomberg data through the new hostname.

**Your Bloomberg AI assistant is ready!**

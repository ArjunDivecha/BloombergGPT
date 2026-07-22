"""
=============================================================================
SCRIPT NAME: bloomberg_keepalive.py
=============================================================================

DESCRIPTION:
    Robust Bloomberg API keepalive service with dual-channel text alerts.
    Pings Bloomberg every 30 seconds, NEVER gives up on failure, and sends
    iMessage + Telegram notifications when the connection goes DOWN or
    comes back UP. Includes a live web dashboard on port 8050.

    KEY BEHAVIORS:
    - Pings 10 tickers in rotation every 30 seconds
    - On failure: progressive backoff retry (never gives up)
    - On UP→DOWN transition: immediate text alert (both iMessage + Telegram)
    - On DOWN→UP transition: immediate text alert
    - During extended DOWN: reminder alerts every 30 minutes
    - Transient blips (1-4 failures): NO alert (avoids spam)
    - VM IP auto-detection on reconnect (handles Parallels network changes)
    - State persisted to disk for crash recovery
    - Dual-channel notifications: iMessage (macOS Messages.app) + Telegram bot

INPUT FILES:
    - /Users/arjundivecha/Dropbox/AAA Backup/A Working/Loop Pilot/looppilot.config.json
      (Telegram credentials fallback if env vars not set)
    - /Users/arjundivecha/Dropbox/AAA Backup/A Working/OpusBloomberg/bbg.py
      (Bloomberg API wrapper — imported at runtime)

OUTPUT FILES:
    - /Users/arjundivecha/Dropbox/AAA Backup/A Working/BloombergGPT/outputs/keepalive_state.json
      (Persistent state: last alert times, connection stats, alert dedup)
    - /Users/arjundivecha/Dropbox/AAA Backup/A Working/BloombergGPT/outputs/keepalive.log
      (Structured JSON-lines log, rotated at 10MB)

VERSION: 2.0
LAST UPDATED: 2026-06-10
AUTHOR: Arjun Divecha

DEPENDENCIES:
    - Python ≥ 3.12 (stdlib only + OpusBloomberg)
    - OpusBloomberg conda environment
    - macOS Messages.app signed into iMessage (for text alerts)
    - Bloomberg Terminal open + logged in on Windows/Parallels

USAGE:
    conda run -p "/Users/arjundivecha/Dropbox/AAA Backup/A Working/OpusBloomberg/.venv" \\
      python "/Users/arjundivecha/Dropbox/AAA Backup/A Working/BloombergGPT/bloomberg_keepalive.py"

    Then open http://localhost:8050 for the live dashboard.

ENVIRONMENT VARIABLES:
    AA_IMESSAGE_TO          — Override iMessage recipient phone (default: +15104212111)
    TELEGRAM_BOT_TOKEN      — Telegram bot token (falls back to looppilot.config.json)
    TELEGRAM_CHAT_ID        — Telegram chat ID (falls back to looppilot.config.json)
    KEEPALIVE_PORT          — Override dashboard HTTP port (default: 8050)
    KEEPALIVE_INTERVAL      — Override ping interval in seconds (default: 30)
    KEEPALIVE_DOWN_REMINDER — Minutes between "still down" reminders (default: 30)

NOTES:
    - This is designed to run forever. Use the companion launchd plist to
      ensure macOS restarts it if it ever crashes:
      /Users/arjundivecha/Library/LaunchAgents/com.arjundivecha.bloomberg-keepalive.plist
    - The program NEVER exits on its own — even if Bloomberg is unreachable
      for hours. It will keep retrying and sending periodic reminders.
    - State is written atomically (write-then-rename) to avoid corruption.
=============================================================================
"""

import sys
import os
import json
import time
import threading
import subprocess
import urllib.request
import urllib.parse
import logging
import logging.handlers
import signal
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Bloomberg imports ──────────────────────────────────────────────────
sys.path.insert(0, '/Users/arjundivecha/Dropbox/AAA Backup/A Working/OpusBloomberg')
from bbg import BBG

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  CONFIGURATION                                                          ║
# ╚══════════════════════════════════════════════════════════════════════════╝

PORT                = int(os.environ.get("KEEPALIVE_PORT", "8050"))
INTERVAL            = int(os.environ.get("KEEPALIVE_INTERVAL", "30"))        # seconds between pings
DOWN_REMINDER_MIN   = int(os.environ.get("KEEPALIVE_DOWN_REMINDER", "30"))   # minutes between "still down" alerts
FAIL_THRESHOLD      = 5                                                      # consecutive failures to declare DOWN
BACKOFF_BASE        = 5                                                      # base backoff seconds after each failed reconnect
BACKOFF_MAX         = 300                                                    # max backoff (5 minutes)
DEGRADED_THRESHOLD  = 1                                                      # failures before entering DEGRADED state

IMESSAGE_RECIPIENT  = os.environ.get("AA_IMESSAGE_TO", "+15104212111")

BASE_DIR            = Path("/Users/arjundivecha/Dropbox/AAA Backup/A Working/BloombergGPT")
OUTPUT_DIR          = BASE_DIR / "outputs"
STATE_FILE          = OUTPUT_DIR / "keepalive_state.json"
LOG_FILE            = OUTPUT_DIR / "keepalive.log"
LOOP_PILOT_CONFIG   = Path("/Users/arjundivecha/Dropbox/AAA Backup/A Working/Loop Pilot/looppilot.config.json")

TICKERS = [
    ("AAPL US Equity",   ["PX_LAST", "NAME"]),
    ("MSFT US Equity",   ["PX_LAST", "PE_RATIO"]),
    ("SPX Index",        ["PX_LAST", "CHG_PCT_1D"]),
    ("USDJPY Curncy",    ["PX_LAST", "NAME"]),
    ("GT10 Govt",        ["PX_LAST", "NAME"]),
    ("GOOGL US Equity",  ["PX_LAST", "CUR_MKT_CAP"]),
    ("CL1 Comdty",       ["PX_LAST", "NAME"]),
    ("GC1 Comdty",       ["PX_LAST", "NAME"]),
    ("NKY Index",        ["PX_LAST", "NAME"]),
    ("EURUSD Curncy",    ["PX_LAST", "NAME"]),
]

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  SHARED STATE (thread-safe via lock)                                    ║
# ╚══════════════════════════════════════════════════════════════════════════╝

lock = threading.Lock()

state = {
    "connection": "UNKNOWN",    # UNKNOWN | UP | DEGRADED | DOWN
    "host": "",
    "start_time": None,         # ISO timestamp when the program started
    "up_since": None,           # ISO timestamp when connection last came UP
    "down_since": None,         # ISO timestamp when connection last went DOWN
    "running": True,
    "consecutive_failures": 0,
    "total_pings": 0,
    "total_ok": 0,
    "total_fail": 0,
    "last_ping_ms": 0,
    "last_alert_state": None,   # "UP" or "DOWN" — for dedup
    "last_down_reminder": None, # ISO timestamp of last "still down" reminder
}

results = []        # list of ping result dicts (last 10,000)
alerts = []         # list of alert dicts (last 500)

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  LOGGING                                                                ║
# ╚══════════════════════════════════════════════════════════════════════════╝

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("keepalive")
logger.setLevel(logging.INFO)

# JSON-lines file handler with rotation
fh = logging.handlers.RotatingFileHandler(
    str(LOG_FILE), maxBytes=10_000_000, backupCount=5
)
fh.setLevel(logging.INFO)
fh.setFormatter(logging.Formatter('{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":%(message)s}'))
logger.addHandler(fh)

# Console handler (human-readable)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s"))
logger.addHandler(ch)

def log_json(level, msg_dict):
    """Log a dict as a JSON string (goes to both console and file)."""
    logger.log(level, json.dumps(msg_dict, default=str))


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  PERSISTENT STATE                                                       ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def load_state():
    """Load persistent state from disk (survives restarts)."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                saved = json.load(f)
            with lock:
                # Only restore alert-dedup fields — runtime state is fresh
                state["last_alert_state"] = saved.get("last_alert_state")
                state["last_down_reminder"] = saved.get("last_down_reminder")
                state["total_pings"] = saved.get("total_pings", 0)
                state["total_ok"] = saved.get("total_ok", 0)
                state["total_fail"] = saved.get("total_fail", 0)
            log_json(logging.INFO, {"event": "state_loaded", "saved": saved})
        except Exception as e:
            log_json(logging.WARNING, {"event": "state_load_failed", "error": str(e)})


def save_state():
    """Atomically persist alert-dedup fields to disk.

    CRITICAL: Callers must hold `lock` before calling this. We do NOT
    re-acquire the lock here because threading.Lock() is not reentrant.
    """
    tmp = str(STATE_FILE) + ".tmp"
    try:
        payload = {
            "last_alert_state": state["last_alert_state"],
            "last_down_reminder": state["last_down_reminder"],
            "total_pings": state["total_pings"],
            "total_ok": state["total_ok"],
            "total_fail": state["total_fail"],
            "updated": datetime.now(timezone.utc).isoformat(),
        }
        with open(tmp, "w") as f:
            json.dump(payload, f, indent=2)
        os.replace(tmp, STATE_FILE)
    except Exception as e:
        log_json(logging.ERROR, {"event": "state_save_failed", "error": str(e)})


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  NOTIFICATION: TELEGRAM                                                 ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def _load_telegram_config():
    """Resolve Telegram credentials: env vars first, then looppilot config."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id_raw = os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat_id_raw:
        return token, int(chat_id_raw)

    if LOOP_PILOT_CONFIG.exists():
        try:
            data = json.loads(LOOP_PILOT_CONFIG.read_text())
            tg = data.get("telegram", {})
            if tg.get("bot_token") and tg.get("chat_id"):
                return tg["bot_token"], int(tg["chat_id"])
        except Exception:
            pass
    return None, None


def send_telegram(text: str) -> bool:
    """Send a Telegram message. Returns True if successful."""
    bot_token, chat_id = _load_telegram_config()
    if not bot_token or not chat_id:
        log_json(logging.WARNING, {"event": "telegram_skip", "reason": "no credentials"})
        return False

    # Chunk long messages (Telegram limit: 4096 chars, we use 3900 to be safe)
    chunks = []
    remaining = text
    while len(remaining) > 3900:
        split_at = remaining.rfind("\n", 0, 3900)
        if split_at < 1950:
            split_at = 3900
        chunks.append(remaining[:split_at].rstrip())
        remaining = remaining[split_at:].lstrip()
    if remaining:
        chunks.append(remaining)

    success = True
    for i, chunk in enumerate(chunks):
        prefix = f"[{i+1}/{len(chunks)}] " if len(chunks) > 1 else ""
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": prefix + chunk,
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                parsed = json.loads(resp.read().decode("utf-8"))
            if not parsed.get("ok"):
                log_json(logging.ERROR, {"event": "telegram_api_error", "response": parsed})
                success = False
        except Exception as e:
            log_json(logging.ERROR, {"event": "telegram_send_failed", "error": str(e)})
            success = False
    return success


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  NOTIFICATION: iMessage (fire-and-forget via osascript)                 ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def send_imessage(text: str, recipient: str = None) -> bool:
    """Send iMessage via osascript. Fire-and-forget — returns immediately.

    Messages.app on modern macOS doesn't respond to AppleEvents within a
    practical timeout, but BlastDoorService delivers the message
    asynchronously. We Popen and return immediately.
    """
    to = recipient or IMESSAGE_RECIPIENT
    safe = text.replace("\\", "\\\\").replace('"', '\\"')
    script = (
        'tell application "Messages"\n'
        '  set targetService to first service whose service type = iMessage\n'
        f'  set targetBuddy to buddy "{to}" of targetService\n'
        f'  send "{safe}" to targetBuddy\n'
        'end tell'
    )
    try:
        subprocess.Popen(
            ["osascript", "-e", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        log_json(logging.INFO, {"event": "imessage_sent", "to": to, "len": len(text)})
        return True
    except Exception as e:
        log_json(logging.ERROR, {"event": "imessage_failed", "error": str(e)})
        return False


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  UNIFIED NOTIFICATION                                                   ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def notify(subject: str, body: str):
    """Send a notification via BOTH iMessage and Telegram.

    iMessage is primary (always attempted).
    Telegram is secondary (only if credentials are configured).
    Failures are logged but never raised — notifications are best-effort.
    """
    full_text = f"{subject}\n\n{body}"

    imessage_ok = send_imessage(full_text)
    telegram_ok = send_telegram(full_text)

    alert_record = {
        "ts": datetime.now().isoformat(),
        "subject": subject,
        "imessage": imessage_ok,
        "telegram": telegram_ok,
    }
    with lock:
        alerts.append(alert_record)
        if len(alerts) > 500:
            alerts.pop(0)

    log_json(logging.INFO, {
        "event": "notify",
        "subject": subject,
        "imessage_ok": imessage_ok,
        "telegram_ok": telegram_ok,
    })


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  CONNECTION STATE MACHINE                                               ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def transition_to(new_state: str):
    """Update connection state and fire alerts on transitions.

    CRITICAL: notify() makes external HTTP calls (Telegram) — it is called
    OUTSIDE the lock to avoid blocking the HTTP dashboard for 15+ seconds.
    """
    pending_notify = None  # (subject, body) tuple if notification needed

    with lock:
        old_state = state["connection"]
        if old_state == new_state:
            return  # no change

        now = datetime.now()
        state["connection"] = new_state

        if new_state == "UP":
            state["up_since"] = now.isoformat()
            state["down_since"] = None
            state["consecutive_failures"] = 0

            # Alert on DOWN→UP or UNKNOWN→UP (recovery)
            if old_state in ("DOWN", "UNKNOWN"):
                downtime = ""
                if old_state == "DOWN":
                    try:
                        ds = datetime.fromisoformat(state.get("_down_start", now.isoformat()))
                        downtime = f"Downtime: ~{_human_duration((now - ds).total_seconds())}\n"
                    except Exception:
                        pass
                pending_notify = (
                    "🟢 Bloomberg Connection RESTORED",
                    f"{downtime}"
                    f"Host: {state['host']}\n"
                    f"Time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Total pings: {state['total_pings']} | "
                    f"OK: {state['total_ok']} | Fail: {state['total_fail']}"
                )
                state["last_alert_state"] = "UP"
                state["last_down_reminder"] = None

        elif new_state == "DOWN":
            state["down_since"] = now.isoformat()
            state["_down_start"] = now.isoformat()
            state["up_since"] = None

            # Alert on any→DOWN (connection lost)
            pending_notify = (
                "🔴 Bloomberg Connection LOST",
                f"Host: {state['host'] or 'not connected'}\n"
                f"Time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Consecutive failures: {state['consecutive_failures']}\n"
                f"Total pings: {state['total_pings']} | "
                f"OK: {state['total_ok']} | Fail: {state['total_fail']}\n\n"
                f"The keepalive will keep retrying and notify you when the connection recovers."
            )
            state["last_alert_state"] = "DOWN"
            state["last_down_reminder"] = now.isoformat()

        elif new_state == "DEGRADED":
            # DEGRADED = transient blips, NO alert (avoids spam)
            pass

        save_state()
        log_json(logging.INFO, {
            "event": "state_transition",
            "old": old_state,
            "new": new_state,
            "failures": state["consecutive_failures"],
        })

    # ── Send notification OUTSIDE the lock ──────────────────────────────
    if pending_notify is not None:
        notify(pending_notify[0], pending_notify[1])


def should_send_down_reminder() -> bool:
    """Check if enough time has passed for a 'still down' reminder."""
    with lock:
        if state["connection"] != "DOWN":
            return False
        if state["last_down_reminder"] is None:
            return True
        try:
            last = datetime.fromisoformat(state["last_down_reminder"])
            if last.tzinfo is None:
                last = last.replace(tzinfo=None)  # naive
            elapsed = (datetime.now() - last).total_seconds()
            return elapsed >= (DOWN_REMINDER_MIN * 60)
        except Exception:
            return True


def mark_down_reminder_sent():
    """Record that a 'still down' reminder was just sent."""
    with lock:
        state["last_down_reminder"] = datetime.now().isoformat()
        save_state()


def _human_duration(seconds: float) -> str:
    """Format seconds as human-readable duration string."""
    if seconds < 120:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds / 60)}m {int(seconds % 60)}s"
    else:
        h = int(seconds / 3600)
        m = int((seconds % 3600) / 60)
        return f"{h}h {m}m"


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  PING LOOP (background thread — the heart of the program)               ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def ping_loop():
    """Main loop: connect, ping, reconnect, repeat. Never exits."""
    global state, results

    # ── Initial connection ──────────────────────────────────────────────
    bbg = None
    backoff = BACKOFF_BASE

    def connect():
        """Attempt to connect to Bloomberg. Returns BBG instance or None."""
        try:
            b = BBG()
            b.connect()
            with lock:
                state["host"] = f"{b.host}:{b.port}"
                state["start_time"] = state["start_time"] or datetime.now().isoformat()
            log_json(logging.INFO, {"event": "connected", "host": state["host"]})
            return b
        except Exception as e:
            log_json(logging.ERROR, {"event": "connect_failed", "error": str(e)})
            return None

    log_json(logging.INFO, {"event": "keepalive_start", "interval": INTERVAL})

    bbg = connect()
    if bbg:
        transition_to("UP")
    else:
        transition_to("DOWN")

    # ── Main ping loop ──────────────────────────────────────────────────
    ping_num = 0
    ticker_idx = 0
    start_time = datetime.now()
    consecutive_connect_fails = 0

    while state["running"]:
        ping_num += 1
        ticker_idx = (ping_num - 1) % len(TICKERS)
        ticker, fields = TICKERS[ticker_idx]
        now = datetime.now()
        t0 = time.perf_counter()

        # ── If we have a session, try a ping ────────────────────────────
        ok = False
        error_msg = None
        data = {}
        ms = 0

        if bbg is not None:
            try:
                data = bbg.ref(ticker, fields)
                ms = round((time.perf_counter() - t0) * 1000, 1)
                has_data = any(v is not None for v in data.values())
                ok = has_data
                if not has_data:
                    error_msg = "All fields returned None"
            except Exception as e:
                ms = round((time.perf_counter() - t0) * 1000, 1)
                error_msg = str(e)
                ok = False

        # ── Update counters ─────────────────────────────────────────────
        with lock:
            state["total_pings"] += 1
            state["last_ping_ms"] = ms
            if ok:
                state["total_ok"] += 1
                state["consecutive_failures"] = 0
            else:
                state["total_fail"] += 1
                state["consecutive_failures"] += 1

            # Append result to ring buffer
            elapsed = now - start_time
            results.append({
                "ping": ping_num,
                "time": now.strftime("%H:%M:%S"),
                "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                "elapsed": str(timedelta(seconds=int(elapsed.total_seconds()))),
                "status": "OK" if ok else "FAIL",
                "ticker": ticker,
                "data": data,
                "ms": ms,
                "error": error_msg,
                "connection_state": state["connection"],
            })
            if len(results) > 10_000:
                results.pop(0)

        # ── Console output ──────────────────────────────────────────────
        icon = "+" if ok else "✗"
        status_line = f"[{icon}] #{ping_num} {now.strftime('%H:%M:%S')} {ticker}: {data} ({ms}ms)"
        if error_msg:
            status_line += f" — {error_msg[:80]}"
        print(status_line)

        # ── State transitions ───────────────────────────────────────────
        cf = state["consecutive_failures"]
        current_conn = state["connection"]

        if ok:
            if current_conn in ("DOWN", "DEGRADED", "UNKNOWN"):
                transition_to("UP")
            consecutive_connect_fails = 0
            backoff = BACKOFF_BASE
        elif cf >= FAIL_THRESHOLD:
            if current_conn != "DOWN":
                transition_to("DOWN")
        elif cf >= DEGRADED_THRESHOLD:
            if current_conn == "UP":
                transition_to("DEGRADED")

        # ── "Still down" reminders ──────────────────────────────────────
        if state["connection"] == "DOWN" and should_send_down_reminder():
            try:
                ds = datetime.fromisoformat(state.get("_down_start", now.isoformat()))
                down_dur = _human_duration((now - ds).total_seconds())
            except Exception:
                down_dur = "unknown"
            notify(
                "🔴 Bloomberg STILL DOWN",
                f"Connection has been DOWN for {down_dur}.\n"
                f"Host: {state['host'] or 'not connected'}\n"
                f"Consecutive failures: {cf}\n"
                f"Total pings: {state['total_pings']} | Fail: {state['total_fail']}\n\n"
                f"Keepalive will continue retrying. Next reminder in {DOWN_REMINDER_MIN} minutes."
            )
            mark_down_reminder_sent()

        # ── Reconnect logic ─────────────────────────────────────────────
        if not ok or bbg is None:
            if bbg is not None:
                try:
                    bbg.disconnect()
                except Exception:
                    pass
                bbg = None

            # Progressive backoff between reconnect attempts
            wait = min(backoff * (1.5 ** consecutive_connect_fails), BACKOFF_MAX)
            log_json(logging.WARNING, {
                "event": "reconnect_wait",
                "backoff_sec": int(wait),
                "consecutive_fails": cf,
                "consecutive_connect_fails": consecutive_connect_fails,
            })

            # Sleep with interruptibility
            for _ in range(int(wait)):
                if not state["running"]:
                    break
                time.sleep(1)

            if not state["running"]:
                break

            log_json(logging.INFO, {"event": "reconnect_attempt", "attempt": consecutive_connect_fails + 1})
            bbg = connect()
            if bbg:
                transition_to("UP")
                consecutive_connect_fails = 0
                backoff = BACKOFF_BASE
            else:
                consecutive_connect_fails += 1
                # Update failure count so state machine sees it
                with lock:
                    state["consecutive_failures"] += 1
                if state["connection"] != "DOWN":
                    transition_to("DOWN")

        # ── Wait between pings (interruptible 1s chunks) ────────────────
        if ok:
            for _ in range(INTERVAL):
                if not state["running"]:
                    break
                time.sleep(1)

    # ── Cleanup ─────────────────────────────────────────────────────────
    if bbg is not None:
        try:
            bbg.disconnect()
        except Exception:
            pass
    log_json(logging.INFO, {"event": "keepalive_stopped"})


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  WEB DASHBOARD                                                          ║
# ╚══════════════════════════════════════════════════════════════════════════╝

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Bloomberg Keepalive — Robust</title>
<style>
  :root {
    --bg: #ffffff;
    --surface: #f6f8fa;
    --border: #d0d7de;
    --text: #1f2328;
    --muted: #656d76;
    --green: #1a7f37;
    --red: #cf222e;
    --yellow: #9a6700;
    --blue: #0969da;
    --radius: 8px;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', sans-serif;
         background: var(--bg); color: var(--text); padding: 24px; line-height: 1.5; }
  .header { display: flex; align-items: center; gap: 12px; margin-bottom: 4px; }
  h1 { font-size: 22px; font-weight: 600; }
  .dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
  .dot-green { background: var(--green); box-shadow: 0 0 8px rgba(26,127,55,0.4); }
  .dot-red { background: var(--red); box-shadow: 0 0 8px rgba(207,34,46,0.4); }
  .dot-yellow { background: var(--yellow); box-shadow: 0 0 8px rgba(154,103,0,0.4); }
  .dot-gray { background: var(--muted); }
  .sub { color: var(--muted); font-size: 13px; margin-bottom: 20px; }
  .state-badge { display: inline-block; padding: 3px 10px; border-radius: 12px;
                 font-size: 12px; font-weight: 600; text-transform: uppercase; }
  .state-up { background: #dafbe1; color: var(--green); }
  .state-down { background: #ffebe9; color: var(--red); }
  .state-degraded { background: #fff8c5; color: var(--yellow); }
  .state-unknown { background: #f6f8fa; color: var(--muted); }

  .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
                gap: 12px; margin-bottom: 24px; }
  .stat-card { background: var(--surface); border: 1px solid var(--border);
               border-radius: var(--radius); padding: 14px 16px; }
  .stat-label { font-size: 11px; color: var(--muted); text-transform: uppercase;
                letter-spacing: 0.5px; margin-bottom: 4px; }
  .stat-value { font-size: 28px; font-weight: 600; }
  .stat-sub { font-size: 12px; color: var(--muted); margin-top: 2px; }
  .green { color: var(--green); }
  .red { color: var(--red); }
  .yellow { color: var(--yellow); }

  .section-title { font-size: 14px; font-weight: 600; text-transform: uppercase;
                   letter-spacing: 0.5px; color: var(--muted); margin-bottom: 8px;
                   margin-top: 20px; }

  table { width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 20px; }
  th { text-align: left; padding: 8px 12px; border-bottom: 2px solid var(--border);
       color: var(--muted); font-weight: 600; font-size: 11px; text-transform: uppercase;
       letter-spacing: 0.5px; background: var(--surface); position: sticky; top: 0; }
  td { padding: 6px 12px; border-bottom: 1px solid var(--border); }
  tr:hover { background: var(--surface); }
  .ok-badge { color: var(--green); font-weight: 600; }
  .fail-badge { color: var(--red); font-weight: 600; }
  .ticker-cell { font-weight: 600; color: var(--blue); }
  .ms-cell { color: var(--muted); }
  .err-cell { color: var(--red); font-size: 11px; max-width: 220px; overflow: hidden;
              text-overflow: ellipsis; white-space: nowrap; }
  .table-wrap { max-height: 420px; overflow-y: auto; border: 1px solid var(--border);
                border-radius: var(--radius); }

  .alert-row { font-size: 12px; }
  .alert-ts { color: var(--muted); white-space: nowrap; }
  .alert-subj { font-weight: 600; }
  .alert-ch { font-size: 11px; }
  .ch-ok { color: var(--green); }
  .ch-fail { color: var(--red); }

  .footer { font-size: 11px; color: var(--muted); margin-top: 16px; text-align: center; }
</style>
</head>
<body>

<div class="header">
  <span class="dot" id="statusDot"></span>
  <h1>Bloomberg Keepalive</h1>
  <span class="state-badge" id="stateBadge"></span>
</div>
<div class="sub" id="subLine">Loading...</div>

<div class="stats-grid">
  <div class="stat-card">
    <div class="stat-label">Total Pings</div>
    <div class="stat-value" id="totalPings">0</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Success</div>
    <div class="stat-value green" id="totalOk">0</div>
    <div class="stat-sub" id="pctOk">—</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Failed</div>
    <div class="stat-value red" id="totalFail">0</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Uptime</div>
    <div class="stat-value" id="uptime">—</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Avg ms</div>
    <div class="stat-value yellow" id="avgMs">—</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Consecutive Fails</div>
    <div class="stat-value red" id="consecFails">0</div>
  </div>
</div>

<div class="section-title">Recent Pings</div>
<div class="table-wrap">
<table>
  <thead><tr>
    <th>#</th><th>Time</th><th>State</th><th>Status</th>
    <th>Ticker</th><th>Data</th><th>ms</th><th>Error</th>
  </tr></thead>
  <tbody id="pingBody"></tbody>
</table>
</div>

<div class="section-title">Alert History</div>
<div class="table-wrap">
<table>
  <thead><tr>
    <th>Time</th><th>Subject</th><th>iMessage</th><th>Telegram</th>
  </tr></thead>
  <tbody id="alertBody"></tbody>
</table>
</div>

<div class="footer">Robust Keepalive v2.0 · Auto-refresh every 3s ·
  <span id="clock"></span></div>

<script>
function fmtData(d) {
  let parts = [];
  for (let k in d) { if (d[k] !== null) parts.push(k + ": " + d[k]); }
  return parts.join(", ");
}

function refresh() {
  fetch("/api/data").then(r => r.json()).then(d => {
    let s = d.status;

    // Status dot
    let dot = document.getElementById("statusDot");
    dot.className = "dot";
    if (s.connection === "UP") dot.classList.add("dot-green");
    else if (s.connection === "DOWN") dot.classList.add("dot-red");
    else if (s.connection === "DEGRADED") dot.classList.add("dot-yellow");
    else dot.classList.add("dot-gray");

    // State badge
    let badge = document.getElementById("stateBadge");
    badge.textContent = s.connection;
    badge.className = "state-badge state-" + s.connection.toLowerCase();

    // Sub-line
    let sub = document.getElementById("subLine");
    if (s.connection === "UP") {
      sub.textContent = "Connected to " + s.host + " · Pinging every 30s";
    } else if (s.connection === "DOWN") {
      sub.textContent = "DISCONNECTED · Retrying with backoff · Alerts active";
    } else if (s.connection === "DEGRADED") {
      sub.textContent = "DEGRADED · Transient failures, monitoring...";
    } else {
      sub.textContent = "Starting up...";
    }

    // Stats
    document.getElementById("totalPings").textContent = s.total_pings;
    document.getElementById("totalOk").textContent = s.total_ok;
    document.getElementById("totalFail").textContent = s.total_fail;
    if (s.total_pings > 0) {
      document.getElementById("pctOk").textContent =
        (s.total_ok / s.total_pings * 100).toFixed(1) + "% success rate";
    }
    document.getElementById("consecFails").textContent = s.consecutive_failures;

    if (d.results.length > 0) {
      let last = d.results[d.results.length - 1];
      document.getElementById("uptime").textContent = last.elapsed;
      let avg = d.results.reduce((sum, r) => sum + r.ms, 0) / d.results.length;
      document.getElementById("avgMs").textContent = Math.round(avg);
    }

    // Ping table
    let pb = document.getElementById("pingBody");
    pb.innerHTML = "";
    let rows = d.results.slice(-50); // last 50
    for (let i = rows.length - 1; i >= 0; i--) {
      let r = rows[i];
      let sc = r.status === "OK" ? "ok-badge" : "fail-badge";
      let stateCls = "state-" + (r.connection_state || "unknown").toLowerCase();
      let tr = document.createElement("tr");
      tr.innerHTML =
        "<td>" + r.ping + "</td>" +
        "<td>" + r.time + "</td>" +
        '<td><span class="state-badge ' + stateCls + '">' + (r.connection_state || "?") + "</span></td>" +
        '<td class="' + sc + '">' + r.status + "</td>" +
        '<td class="ticker-cell">' + r.ticker + "</td>" +
        '<td style="font-family:monospace;font-size:12px;">' + fmtData(r.data) + "</td>" +
        '<td class="ms-cell">' + r.ms + "</td>" +
        '<td class="err-cell" title="' + (r.error || "").replace(/"/g, "&quot;") + '">' + (r.error || "") + "</td>";
      pb.appendChild(tr);
    }

    // Alert table
    let ab = document.getElementById("alertBody");
    ab.innerHTML = "";
    let alerts = d.alerts.slice(-30);
    for (let i = alerts.length - 1; i >= 0; i--) {
      let a = alerts[i];
      let imCls = a.imessage ? "ch-ok" : "ch-fail";
      let tgCls = a.telegram ? "ch-ok" : "ch-fail";
      let tr = document.createElement("tr");
      tr.className = "alert-row";
      tr.innerHTML =
        '<td class="alert-ts">' + a.ts.substring(11, 19) + "</td>" +
        '<td class="alert-subj">' + a.subject + "</td>" +
        '<td class="alert-ch ' + imCls + '">' + (a.imessage ? "✓" : "✗") + "</td>" +
        '<td class="alert-ch ' + tgCls + '">' + (a.telegram ? "✓" : "✗") + "</td>";
      ab.appendChild(tr);
    }

    document.getElementById("clock").textContent = new Date().toLocaleTimeString();
  });
}

refresh();
setInterval(refresh, 3000);
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            with lock:
                payload = {
                    "results": list(results),
                    "alerts": list(alerts),
                    "status": {
                        "connection": state["connection"],
                        "host": state["host"],
                        "start_time": state["start_time"],
                        "up_since": state["up_since"],
                        "down_since": state["down_since"],
                        "total_pings": state["total_pings"],
                        "total_ok": state["total_ok"],
                        "total_fail": state["total_fail"],
                        "consecutive_failures": state["consecutive_failures"],
                        "last_ping_ms": state["last_ping_ms"],
                        "running": state["running"],
                    }
                }
            self.wfile.write(json.dumps(payload, default=str).encode())
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            with lock:
                healthy = state["connection"] in ("UP", "DEGRADED")
            self.wfile.write(json.dumps({"healthy": healthy, "connection": state["connection"]}).encode())
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(HTML.encode())

    def log_message(self, format, *args):
        pass  # suppress HTTP access logs


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  SIGNAL HANDLERS                                                        ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def shutdown(signum=None, frame=None):
    """Graceful shutdown: stop ping loop, close server."""
    log_json(logging.INFO, {"event": "shutdown", "signal": str(signum)})
    with lock:
        state["running"] = False
    # Give the ping thread a moment to clean up
    time.sleep(1)
    sys.exit(0)


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  MAIN                                                                   ║
# ╚══════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    print("=" * 60)
    print("  Bloomberg Robust Keepalive v2.0")
    print("=" * 60)
    print(f"  Dashboard:    http://localhost:{PORT}")
    print(f"  Ping interval: {INTERVAL}s")
    print(f"  Down reminder: every {DOWN_REMINDER_MIN} min")
    print(f"  Alerts:       iMessage → {IMESSAGE_RECIPIENT}")
    tg_token, tg_chat = _load_telegram_config()
    print(f"  Telegram:     {'configured (chat ' + str(tg_chat) + ')' if tg_token else 'NOT configured'}")
    print(f"  State file:   {STATE_FILE}")
    print(f"  Log file:     {LOG_FILE}")
    print("=" * 60)
    print()

    # Load persistent state from prior run
    load_state()

    # Register signal handlers for clean shutdown
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Start ping loop in background daemon thread
    ping_thread = threading.Thread(target=ping_loop, daemon=True, name="bloomberg-ping")
    ping_thread.start()

    # Send startup notification
    time.sleep(2)  # Let the initial connection attempt settle
    conn_state = state["connection"]
    if conn_state == "DOWN":
        notify(
            "⚠️ Bloomberg Keepalive Started — Connection DOWN",
            f"The keepalive service has started but Bloomberg is NOT reachable.\n"
            f"Host attempted: {state['host'] or 'unknown'}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"Retrying forever with progressive backoff. You'll be notified when it recovers."
        )
    else:
        log_json(logging.INFO, {"event": "startup", "connection": conn_state})

    # Start web server (main thread)
    # Allow immediate rebind after crash (SO_REUSEADDR)
    import socketserver
    socketserver.TCPServer.allow_reuse_address = True
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    try:
        log_json(logging.INFO, {"event": "http_server_start", "port": PORT})
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        shutdown()

"""
=============================================================================
SCRIPT NAME: keepalive_dashboard.py
=============================================================================

DESCRIPTION:
    Live web dashboard that pings Bloomberg every 30 seconds and displays
    results in a browser. Runs a background thread that queries Bloomberg
    reference data for a rotating set of tickers, and serves status via an
    embedded HTTP server on port 8050. Auto-reconnects after 5 consecutive
    failures.

INPUT FILES:
    (none -- Bloomberg data is fetched live via OpusBloomberg)

OUTPUT FILES:
    (none -- data is served in-memory via HTTP API at /api/data)

VERSION: 1.0
LAST UPDATED: 2026-06-05
AUTHOR: Arjun Divecha

DEPENDENCIES:
    - OpusBloomberg.bbg (from /Users/arjundivecha/Dropbox/AAA Backup/A Working/OpusBloomberg)
    - Python stdlib: http.server, threading, json, time

USAGE:
    conda run -p "/Users/arjundivecha/Dropbox/AAA Backup/A Working/OpusBloomberg/.venv" \
      python "/Users/arjundivecha/Dropbox/AAA Backup/A Working/BloombergGPT/keepalive_dashboard.py"
    Then open http://localhost:8050

NOTES:
    - Bloomberg Terminal must be open and logged in on the host.
    - Requires OpusBloomberg conda environment.
    - Pings 10 tickers in rotation; each ping resolves one ticker.
    - The dashboard front-end auto-refreshes every 3 seconds.
=============================================================================
"""

import sys
import os
import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta

sys.path.insert(0, '/Users/arjundivecha/Dropbox/AAA Backup/A Working/OpusBloomberg')
from bbg import BBG

# =============================================================================
# CONFIG
# =============================================================================

PORT = 8050
INTERVAL = 30  # seconds between pings

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

# Shared state
results = []
status = {"connected": False, "host": "", "start_time": None, "running": True}
lock = threading.Lock()

# =============================================================================
# BLOOMBERG PING LOOP (background thread)
# =============================================================================

def ping_loop():
    global results, status

    print("Connecting to Bloomberg...")
    try:
        bbg = BBG()
        bbg.connect()
        status["connected"] = True
        status["host"] = f"{bbg.host}:{bbg.port}"
        status["start_time"] = datetime.now().isoformat()
        print(f"Connected to {bbg.host}:{bbg.port}")
    except Exception as e:
        print(f"FATAL: {e}")
        status["connected"] = False
        status["running"] = False
        return

    ping_num = 0
    start_time = datetime.now()
    consecutive_failures = 0

    while status["running"]:
        ping_num += 1
        idx = (ping_num - 1) % len(TICKERS)
        ticker, fields = TICKERS[idx]

        now = datetime.now()
        elapsed = now - start_time
        t0 = time.perf_counter()

        try:
            data = bbg.ref(ticker, fields)
            ms = round((time.perf_counter() - t0) * 1000, 1)
            has_data = any(v is not None for v in data.values())
            ok = has_data
            error = None if has_data else "All fields returned None"
            if not has_data:
                consecutive_failures += 1
            else:
                consecutive_failures = 0
        except Exception as e:
            ms = round((time.perf_counter() - t0) * 1000, 1)
            data = {}
            ok = False
            error = str(e)
            consecutive_failures += 1

        row = {
            "ping": ping_num,
            "time": now.strftime("%H:%M:%S"),
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed": str(timedelta(seconds=int(elapsed.total_seconds()))),
            "status": "OK" if ok else "FAIL",
            "ticker": ticker,
            "data": data,
            "ms": ms,
            "error": error,
        }

        with lock:
            results.append(row)

        icon = "+" if ok else "X"
        print(f"  [{icon}] #{ping_num} {now.strftime('%H:%M:%S')} {ticker}: {data} ({ms}ms)")

        # Reconnect after 5 consecutive failures
        if consecutive_failures == 5:
            print("  >>> 5 failures, reconnecting...")
            try:
                bbg.disconnect()
                time.sleep(2)
                bbg = BBG()
                bbg.connect()
                status["host"] = f"{bbg.host}:{bbg.port}"
                print(f"  >>> Reconnected to {bbg.host}")
                consecutive_failures = 0
            except Exception as e:
                print(f"  >>> Reconnect failed: {e}")

        if consecutive_failures >= 10:
            print("  >>> 10 consecutive failures. Session dead.")
            status["connected"] = False
            break

        # Wait
        for _ in range(INTERVAL):
            if not status["running"]:
                break
            time.sleep(1)

    try:
        bbg.disconnect()
    except Exception:
        pass


# =============================================================================
# WEB SERVER
# =============================================================================

HTML = """<!DOCTYPE html>
<html>
<head>
<title>Bloomberg Keepalive Dashboard</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', Helvetica, sans-serif;
         background: #0d1117; color: #e6edf3; padding: 20px; }
  h1 { font-size: 22px; font-weight: 600; margin-bottom: 4px; }
  .sub { color: #8b949e; font-size: 13px; margin-bottom: 16px; }
  .stats { display: flex; gap: 24px; margin-bottom: 16px; }
  .stat { background: #161b22; border: 1px solid #30363d; border-radius: 8px;
          padding: 12px 18px; min-width: 120px; }
  .stat-label { font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 0.5px; }
  .stat-value { font-size: 24px; font-weight: 600; margin-top: 2px; }
  .green { color: #3fb950; }
  .red { color: #f85149; }
  .yellow { color: #d29922; }
  table { width: 100%%; border-collapse: collapse; font-size: 13px; }
  th { text-align: left; padding: 8px 12px; border-bottom: 2px solid #30363d;
       color: #8b949e; font-weight: 600; font-size: 11px; text-transform: uppercase;
       letter-spacing: 0.5px; position: sticky; top: 0; background: #0d1117; }
  td { padding: 6px 12px; border-bottom: 1px solid #21262d; }
  tr:hover { background: #161b22; }
  .ok { color: #3fb950; font-weight: 600; }
  .fail { color: #f85149; font-weight: 600; }
  .data-cell { font-family: 'SF Mono', Menlo, monospace; font-size: 12px; }
  .ticker { font-weight: 600; color: #79c0ff; }
  .ms { color: #8b949e; }
  .error-cell { color: #f85149; font-size: 11px; }
  .table-wrap { max-height: calc(100vh - 200px); overflow-y: auto; }
  .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%%;
         margin-right: 6px; position: relative; top: -1px; }
  .dot-green { background: #3fb950; box-shadow: 0 0 6px #3fb950; }
  .dot-red { background: #f85149; box-shadow: 0 0 6px #f85149; }
</style>
</head>
<body>
<h1><span class="dot" id="dot"></span>Bloomberg Keepalive Dashboard</h1>
<div class="sub" id="sub">Connecting...</div>
<div class="stats">
  <div class="stat"><div class="stat-label">Pings</div><div class="stat-value" id="total">0</div></div>
  <div class="stat"><div class="stat-label">Success</div><div class="stat-value green" id="ok">0</div></div>
  <div class="stat"><div class="stat-label">Failed</div><div class="stat-value red" id="fail">0</div></div>
  <div class="stat"><div class="stat-label">Uptime</div><div class="stat-value" id="uptime">-</div></div>
  <div class="stat"><div class="stat-label">Avg ms</div><div class="stat-value yellow" id="avgms">-</div></div>
</div>
<div class="table-wrap">
<table>
<thead><tr>
  <th>#</th><th>Time</th><th>Elapsed</th><th>Status</th>
  <th>Ticker</th><th>Data</th><th>ms</th><th>Error</th>
</tr></thead>
<tbody id="tbody"></tbody>
</table>
</div>
<script>
function fmt(d) {
  let parts = [];
  for (let k in d) { if (d[k] !== null) parts.push(k + ": " + d[k]); }
  return parts.join(", ");
}
function refresh() {
  fetch("/api/data").then(r => r.json()).then(d => {
    let dot = document.getElementById("dot");
    let sub = document.getElementById("sub");
    dot.className = d.status.connected ? "dot dot-green" : "dot dot-red";
    sub.textContent = d.status.connected
      ? "Connected to " + d.status.host + " | Pinging every 30s"
      : "Disconnected";

    let rows = d.results;
    let ok = rows.filter(r => r.status === "OK").length;
    let fail = rows.length - ok;
    document.getElementById("total").textContent = rows.length;
    document.getElementById("ok").textContent = ok;
    document.getElementById("fail").textContent = fail;
    if (rows.length > 0) {
      document.getElementById("uptime").textContent = rows[rows.length-1].elapsed;
      let avg = rows.reduce((s,r) => s + r.ms, 0) / rows.length;
      document.getElementById("avgms").textContent = Math.round(avg);
    }

    let tbody = document.getElementById("tbody");
    tbody.innerHTML = "";
    for (let i = rows.length - 1; i >= 0; i--) {
      let r = rows[i];
      let tr = document.createElement("tr");
      let sc = r.status === "OK" ? "ok" : "fail";
      tr.innerHTML = "<td>" + r.ping + "</td>"
        + "<td>" + r.time + "</td>"
        + "<td>" + r.elapsed + "</td>"
        + '<td class="' + sc + '">' + r.status + "</td>"
        + '<td class="ticker">' + r.ticker + "</td>"
        + '<td class="data-cell">' + fmt(r.data) + "</td>"
        + '<td class="ms">' + r.ms + "</td>"
        + '<td class="error-cell">' + (r.error || "") + "</td>";
      tbody.appendChild(tr);
    }
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
            self.end_headers()
            with lock:
                payload = {"results": list(results), "status": dict(status)}
            self.wfile.write(json.dumps(payload).encode())
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(HTML.encode())

    def log_message(self, format, *args):
        pass  # suppress request logs


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print(f"Starting Bloomberg Keepalive Dashboard on http://localhost:{PORT}")
    print(f"Ping interval: {INTERVAL}s")
    print()

    # Start ping loop in background thread
    t = threading.Thread(target=ping_loop, daemon=True)
    t.start()

    # Start web server
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        status["running"] = False
        server.shutdown()

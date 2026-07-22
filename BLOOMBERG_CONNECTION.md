# Bloomberg API Connection Guide

**READ THIS FIRST** if you need to connect to Bloomberg from any Python script on this Mac.

---

## The Short Version (copy-paste this)

```python
import sys
sys.path.insert(0, '/Users/arjundivecha/Dropbox/AAA Backup/A Working/OpusBloomberg')
from bbg import BBG, bloomberg_setup

bloomberg_setup()  # One-time: starts bbcomm, sets up port forwarding, tests connection

with BBG() as bbg:
    data = bbg.ref("AAPL US Equity", ["PX_LAST", "NAME"])
    print(data)
```

Run with the OpusBloomberg conda env:
```bash
conda run -p "/Users/arjundivecha/Dropbox/AAA Backup/A Working/OpusBloomberg/.venv" python your_script.py
```

That's it. The VM IP is auto-detected. You do NOT need to know or hardcode any IP address.

---

## How It Works (the full chain)

```
Your Python script (macOS)
    │
    │  TCP port 8194
    ▼
Windows 11 VM in Parallels (IP auto-detected)
    │
    │  netsh port forwarding rule
    ▼
bbcomm.exe (127.0.0.1:8194) — Bloomberg's BLPAPI communications server
    │
    ▼
Bloomberg Terminal ──> Bloomberg Servers (internet)
```

### Why the IP is tricky

Parallels can assign the Windows VM different IP addresses depending on its
networking mode:

| Parallels Mode | VM Subnet | Example IP |
|---|---|---|
| **Shared** (default) | `10.211.55.x` | `10.211.55.3` |
| **Bridged** | Same as your LAN | `10.0.1.16` |

The mode can change without warning (Parallels updates, network changes, etc.).
The `BBG()` class handles this automatically by:

1. Running `ipconfig` on the VM via `prlctl exec`
2. Collecting all IPv4 addresses
3. Testing TCP connectivity to port 8194 on each one
4. Setting up port forwarding (`netsh`) if needed
5. Using the first IP that works

**You never need to hardcode an IP.** Just use `BBG()` with no arguments.

---

## Prerequisites (before your script can run)

1. **Parallels** must be running with the "Windows 11" VM started
2. **Bloomberg Terminal** must be open and logged in on the Windows side
3. **bbcomm.exe** must be running (bloomberg_setup() starts it if needed)

### First time after a reboot?

bbcomm.exe does not survive Windows reboots. Call `bloomberg_setup()` once
after each reboot — it will start bbcomm and configure port forwarding.

### Locked terminal?

Bloomberg's lock screen (B-Unit password screen) does NOT kill the API
connection. DDE and BLPAPI keep working through lock/unlock cycles. Only a
full logout or logging into Bloomberg Terminal mode on iPad kills the session.

---

## The Conda Environment

All Bloomberg scripts MUST use the OpusBloomberg conda env because `blpapi`
is installed there:

```bash
# Run any script
conda run -p "/Users/arjundivecha/Dropbox/AAA Backup/A Working/OpusBloomberg/.venv" python your_script.py

# Install additional packages
conda install -p "/Users/arjundivecha/Dropbox/AAA Backup/A Working/OpusBloomberg/.venv" -c conda-forge <package>
```

Pre-installed: `blpapi 3.25.12.1`, `pandas`, `numpy`, `openpyxl`, `matplotlib`, `scipy`

---

## API Quick Reference

```python
with BBG() as bbg:
    # Current data — single ticker
    data = bbg.ref("AAPL US Equity", ["PX_LAST", "NAME", "CUR_MKT_CAP"])

    # Current data — multiple tickers
    batch = bbg.ref_batch(
        ["AAPL US Equity", "MSFT US Equity", "GOOGL US Equity"],
        ["PX_LAST", "PE_RATIO"]
    )

    # Historical time series (dates in YYYYMMDD format)
    history = bbg.hist("AAPL US Equity", "PX_LAST", "20250101", "20260201")

    # Connection health check
    alive = bbg.ping()  # Returns True/False
```

### Ticker formats
| Type | Format | Example |
|---|---|---|
| US Equity | `"TICKER US Equity"` | `"AAPL US Equity"` |
| Int'l Equity | `"CODE CC Equity"` | `"7203 JP Equity"` |
| Index | `"CODE Index"` | `"SPX Index"`, `"NKY Index"` |
| FX | `"CCCCCC Curncy"` | `"USDJPY Curncy"` |
| Govt Bond | `"CODE Govt"` | `"GT10 Govt"` |
| Commodity | `"CODE Comdty"` | `"CL1 Comdty"` (WTI), `"GC1 Comdty"` (gold) |

### Common fields
| Field | Description |
|---|---|
| `PX_LAST` | Last price |
| `PX_OPEN`, `PX_HIGH`, `PX_LOW` | OHLC |
| `PX_VOLUME` | Volume |
| `NAME` | Security name |
| `CUR_MKT_CAP` | Market cap |
| `PE_RATIO` | P/E ratio |
| `PX_TO_BOOK_RATIO` | Price to book |
| `EQY_DVD_YLD_IND` | Dividend yield |
| `BEST_EPS`, `BEST_SALES` | Consensus estimates |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ConnectionError: Failed to start Bloomberg session` | bbcomm not running or port forwarding stale | Run `bloomberg_setup()` |
| `ConnectionError: Cannot reach Bloomberg on any VM IP` | VM not running or Bloomberg not started | Start Parallels + Bloomberg Terminal |
| Works from one script but not another | Wrong conda env | Use `conda run -p ".../OpusBloomberg/.venv"` |
| Was working, suddenly stopped | Parallels changed VM IP (networking mode switch) | Auto-detection handles this — just retry |
| `ImportError: No module named 'blpapi'` | Not using the conda env | See conda section above |

---

## Files Reference

| File | Location | Purpose |
|---|---|---|
| `bbg.py` | OpusBloomberg | `BBG` class + `detect_vm_ip()` + `bloomberg_setup()` |
| `bloomberg_connect.py` | OpusBloomberg | Full 7-step connection setup (bbcomm, port forward, firewall, test) |
| `.venv/` | OpusBloomberg | Conda env with blpapi and all dependencies |

**Library location:** `/Users/arjundivecha/Dropbox/AAA Backup/A Working/OpusBloomberg`

---

Last Updated: 2026-02-20

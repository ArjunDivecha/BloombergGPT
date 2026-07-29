"""
=============================================================================
SCRIPT NAME: ArjunBloomberg.py
=============================================================================

INPUT FILES:
- /Users/arjundivecha/Dropbox/AAA Backup/A Working/BloombergGPT/PRTU.xlsx
  Existing Bloomberg BBU portfolio-upload template. Sheet "Book1" contains
  one contiguous row-block per portfolio (PORTFOLIO NAME in column B).
  Live data (none) - all position data below comes from the Schwab API.

- /Users/arjundivecha/Dropbox/AAA Backup/A Working/BloombergGPT/ibkr_fetch_full.py
  This project's IBKR position-fetch script. Invoked as a subprocess under
  News' .venv-ibkr312 interpreter (ib_insync requires Python 3.12) against a
  locally running, logged-in LIVE IB Gateway/TWS session (port auto-detected,
  see IBKR_CANDIDATE_PORTS). Emits futures-detail fields (local_symbol/expiry/multiplier)
  needed to build Bloomberg futures tickers.

OUTPUT FILES:
- /Users/arjundivecha/Dropbox/AAA Backup/A Working/BloombergGPT/PRTU.xlsx
  Overwritten in place. Replaces the row-blocks for the five Schwab-backed
  portfolios (COUNTRYMOM, COUNTRYVAL, IRAMOM, MUNI, SCHWAB) and all three
  IBKR-backed ones (IBKRMAIN, IBKREXPERIMENT, IBKRLONGSHORT). Header/notes
  rows are left untouched.
- /Users/arjundivecha/Dropbox/AAA Backup/A Working/BloombergGPT/prtu_backups/
  PRTU_backup_YYYYMMDD_HHMMSS.xlsx
  Timestamped backup of PRTU.xlsx written BEFORE any overwrite (Bloomberg
  upload data is precious - never overwrite without a backup first).

VERSION: 1.1
LAST UPDATED: 2026-07-22
AUTHOR: Assistant

DESCRIPTION:
Refreshes the Schwab- and IBKR-sourced portfolio blocks in PRTU.xlsx
directly from live broker data, instead of hand-maintaining them.

Five of Arjun's seven linked Schwab accounts map 1:1 to existing portfolio
blocks in PRTU.xlsx, keyed off the Schwab account NICKNAME (from the
`preferences` endpoint), which is far more reliable than matching on
holdings snapshots:

    Schwab nickname     -> Schwab account #  -> PRTU portfolio block
    "Joint"              -> 28739966          -> SCHWAB
    "Equity Momentum"    -> 76705090          -> COUNTRYMOM
    "Equity Value"       -> 12790167          -> COUNTRYVAL
    "Arjun IRA"          -> 28739970          -> IRAMOM
    "AA"                 -> 36563696          -> MUNI

Two linked accounts ("Dancing Elephant" / 36959647 and "TD Ameritrade" /
50913476) do NOT correspond to any existing PRTU block and are
deliberately skipped (per explicit instruction, 2026-07-22).

For each mapped account, every open position is translated into a BBU row:
    - Column B  PORTFOLIO NAME   = the mapped block name above
    - Column C  SECURITY_ID      = "{symbol} US" when Schwab reports a real
                                    trading symbol (symbol != cusip)
    - Column E  SECURITY_ID      = the CUSIP, used instead of column C when
                                    Schwab has no real trading symbol (its
                                    "symbol" field is literally the CUSIP -
                                    e.g. delisted/OTC/restricted holdings)
    - Column G  (description)    = Schwab's instrument description, or the
                                    symbol/CUSIP if no description is given
    - Column H  QUANTITY         = longQuantity - shortQuantity, scaled by
                                    1000 for FIXED_INCOME positions (Schwab
                                    quotes bond quantity in $1000-face
                                    "bonds"; the BBU template wants face
                                    value per its own column-2 note)
    - Column K  Cost Price       = Schwab's averagePrice
    - Column L  As of Date       = the timestamp this script ran
    - Column M  Custom grouping  = derived from Schwab assetType:
                                    EQUITY -> "US Equities"
                                    COLLECTIVE_INVESTMENT -> "ETFs"
                                    MUTUAL_FUND -> "Mutual Funds"
                                    FIXED_INCOME -> "All Fixed Income"
                                    (cash always -> "Portfolio Cash")
A trailing CASH CASH row is added per portfolio from the account's cash
balance (currentBalances.cashBalance).

Positions with neither a usable symbol nor a CUSIP (Schwab sometimes
returns a bare position with instrument fields all None - seen for a
couple of zero-cost-basis legacy holdings) CANNOT be safely identified and
are skipped with a printed warning rather than guessed at (no fabricated
security IDs - see repo's "FAIL IS FAIL" policy). Review these manually in
the Schwab UI if the warning appears.

IBKR SECTION:
All 3 IBKR accounts are visible on the live TWS API session and map
1:1 to the three IBKR blocks. Verified 2026-07-22: each account's live
holdings matched that block's existing hand-maintained holdings exactly.

    IBKR account -> PRTU portfolio block
    U1399611      -> IBKRMAIN         (CEE, INTC, CORD, SCHW, COPX, ...)
    U14983106     -> IBKREXPERIMENT   (XBI, XLY, KRE, XLC, IHI, KBE)
    U24887919     -> IBKRLONGSHORT    (no positions, cash only)

IMPORTANT - live vs paper: a paper-trading session exposes simulated
"DU"/"DF"-prefixed accounts whose holdings are unrelated to the real
portfolios; writing those into PRTU.xlsx silently corrupts the real blocks
(this happened on 2026-07-22 from the paper Gateway). Live-vs-paper is
decided from the ACCOUNT PREFIX, never the port number, because the IBKR
port defaults are only conventions and are user-configurable - on this
machine live TWS serves 7497 while 4002 is the paper Gateway. The script
probes every candidate port and uses the first session whose accounts are
not paper-prefixed (see IBKR_CANDIDATE_PORTS / fetch_ibkr_live).

Each IBKR position becomes a BBU row the same way as Schwab positions:
    - STK positions are written as equities (see ticker rule below).
    - FUT positions are written using a verified Bloomberg futures ticker
      (IBKR_FUT_ROOT_TO_BBG + the localSymbol month/year code); a future
      whose root is not in that map is skipped and reported, never guessed.
    - Any other instrument type (options, etc.) is skipped with a warning.
    - Ticker is "{symbol} {exchange}", where exchange is derived from the
      position's trading currency via CURRENCY_TO_BBG_EXCHANGE, so non-USD
      holdings resolve on their local exchange: ETM (AUD) -> "ETM AU",
      IES (GBP) -> "IES LN". NOTE this corrects the old hand-maintained
      file, which listed both as "... US". A currency with no mapping is
      skipped and reported, never defaulted to " US".
    - Cost Price = IBKR's avgCost (already per-share for stocks).
    - Custom grouping is always "US Equities" (matches existing convention;
      the workbook has no international-equity grouping).

DEPENDENCIES:
- schwabdev
- openpyxl
- News project's .venv-ibkr312 + ib_insync (invoked as a subprocess only,
  not imported directly - this project's own Python does not need
  ib_insync installed)

USAGE:
  python3 ArjunBloomberg.py

NOTES:
- Schwab OAuth token cache is shared system-wide at ~/.schwabdev/tokens.db
  and is already authenticated; no interactive login is needed as long as
  that cache stays valid. If it expires, schwabdev will print a login URL.
- App key/secret are read from the SCHWAB_CLIENT_ID / SCHWAB_CLIENT_SECRET
  environment variables, falling back to those same keys in
  /Users/arjundivecha/Dropbox/AAA Backup/.env.txt. They are NEVER hardcoded
  in this file - this repo is public. A missing credential raises rather
  than silently failing at the auth step.
- LIVE TWS or IB Gateway must be running and logged in on 127.0.0.1. The
  port is auto-detected across IBKR_CANDIDATE_PORTS and validated by account
  prefix. If no live session is found, the IBKR portion is skipped with a
  warning and the IBKR blocks are left untouched (Schwab blocks still update
  normally). Paper sessions are rejected - see IBKR SECTION.
- Does NOT touch any header/notes rows.
=============================================================================
"""

import json
import os
import shutil
import socket
import subprocess
from datetime import datetime

import openpyxl
import schwabdev

PRTU_PATH = "/Users/arjundivecha/Dropbox/AAA Backup/A Working/BloombergGPT/PRTU.xlsx"
BACKUP_DIR = "/Users/arjundivecha/Dropbox/AAA Backup/A Working/BloombergGPT/prtu_backups"
ENV_FILE = "/Users/arjundivecha/Dropbox/AAA Backup/.env.txt"

# NOTE: credentials are NEVER hardcoded here - this repo is public. They are
# read at runtime from ENV_FILE (or the process environment); see
# load_schwab_credentials(), which fails loudly if they are absent.
SCHWAB_KEY_VAR = "SCHWAB_CLIENT_ID"
SCHWAB_SECRET_VAR = "SCHWAB_CLIENT_SECRET"

# IBKR access. Reuse News' .venv-ibkr312 interpreter (it has ib_insync on
# Python 3.12), but run this project's own fetch script - ibkr_fetch_full.py
# emits the extra futures-detail fields (local_symbol, expiry, multiplier)
# that News' ibkr_fetch.py omits and that futures ticker construction needs.
IBKR_PYTHON = "/Users/arjundivecha/Dropbox/AAA Backup/A Working/News/.venv-ibkr312/bin/python3"
IBKR_FETCH_SCRIPT = "/Users/arjundivecha/Dropbox/AAA Backup/A Working/BloombergGPT/ibkr_fetch_full.py"

# Candidate IBKR API ports, probed in this order.
#
# Do NOT infer live-vs-paper from the port number. The IBKR defaults (live
# 7496/4001, paper 7497/4002) are only conventions and are user-configurable:
# on this machine TWS serves the three REAL accounts on 7497, while 4002 is the
# paper Gateway. An earlier version of this script hard-coded the conventional
# live ports and therefore skipped the real session entirely (2026-07-29).
#
# The authoritative live-vs-paper signal is the ACCOUNT PREFIX: IBKR paper
# accounts are "DU"/"DF"-prefixed. fetch_ibkr_live() probes each reachable port
# and accepts the first one whose accounts are not paper, so simulated holdings
# can never overwrite the real portfolio blocks regardless of port numbering.
IBKR_CANDIDATE_PORTS = [7496, 4001, 7497, 4002]
IBKR_PAPER_ACCOUNT_PREFIXES = ("DU", "DF")
IBKR_CLIENT_ID = 209  # distinct from News' own client id (103) to avoid session collisions

# IBKR position currency -> Bloomberg exchange code used in SECURITY_ID.
# IBKR's reqPositions() gives the trading currency but not an exchange, so the
# currency is what we key off. Deliberately a STRICT lookup: a currency that is
# not listed here is skipped with a loud warning rather than defaulting to " US"
# and silently pointing Bloomberg at the wrong (or a non-existent) security.
CURRENCY_TO_BBG_EXCHANGE = {
    "USD": "US",
    "AUD": "AU",   # ASX      (e.g. ETM -> "ETM AU")
    "GBP": "LN",   # LSE      (e.g. IES -> "IES LN")
}

# IBKR account number -> PRTU.xlsx portfolio block name.
# Confirmed 2026-07-22 against live TWS: each account's live
# holdings matched the corresponding block's existing holdings exactly.
IBKR_ACCOUNT_TO_PORTFOLIO = {
    "U1399611": "IBKRMAIN",
    "U14983106": "IBKREXPERIMENT",
    "U24887919": "IBKRLONGSHORT",
}

# IBKR futures root -> (Bloomberg root, Bloomberg yellow-key sector).
# Every mapping VERIFIED live against Bloomberg on 2026-07-28: for each held
# contract, the Bloomberg ticker built as f"{bbg_root}{month_year} {sector}"
# resolved to a security whose LAST_TRADEABLE_DT and FUT_CONT_SIZE both matched
# what IBKR reported (2-way cross-check) - e.g. IBKR M6AZ6 -> CRDZ6 Curncy =
# "Micro AUD/USD Dec26", LTD 2026-12-14, size 10000.
#   IBKR sym  product                      BBG root  sector
#   M6A       Micro AUD/USD (CME)          CRD       Curncy
#   MJY       Micro JPY/USD (CME)          MJY       Curncy
#   MHG       Micro Copper (COMEX)         MHC       Comdty
#   MCL       Micro WTI Crude (NYMEX)      WMI       Comdty
#   QG        E-mini Natural Gas (NYMEX)   EO        Comdty
# The month+year code (e.g. "Z6") is taken verbatim from IBKR's localSymbol,
# which uses the same code Bloomberg accepted. STRICT lookup: an IBKR future
# whose root is NOT here is skipped with a loud warning, never guessed - a
# wrong futures ticker points Bloomberg at the wrong contract.
IBKR_FUT_ROOT_TO_BBG = {
    "M6A": ("CRD", "Curncy"),
    "MJY": ("MJY", "Curncy"),
    "MHG": ("MHC", "Comdty"),
    "MCL": ("WMI", "Comdty"),
    "QG":  ("EO",  "Comdty"),
}

# Schwab account nickname -> PRTU.xlsx portfolio block name.
# Confirmed 2026-07-22 against live Schwab preferences() nicknames and
# cross-checked against each block's existing holdings.
NICKNAME_TO_PORTFOLIO = {
    "Joint": "SCHWAB",
    "Equity Momentum": "COUNTRYMOM",
    "Equity Value": "COUNTRYVAL",
    "Arjun IRA": "IRAMOM",
    "AA": "MUNI",
}

# Order the rebuilt blocks are written in (matches the original file's order)
PORTFOLIO_ORDER = ["COUNTRYMOM", "COUNTRYVAL", "IRAMOM", "MUNI", "SCHWAB"]

ASSET_TYPE_TO_GROUPING = {
    "EQUITY": "US Equities",
    "COLLECTIVE_INVESTMENT": "ETFs",
    "MUTUAL_FUND": "Mutual Funds",
    "FIXED_INCOME": "All Fixed Income",
}

# SECURITY_ID written for the per-portfolio cash row (column C).
CASH_SECURITY_ID = "CASH CASH"

# Broker symbol -> the symbol to use when building the Bloomberg ticker.
# Schwab reports the SES rights/when-issued line as "SES+", which Bloomberg
# does not resolve; it is uploaded as plain SES (Arjun, 2026-07-24). Note this
# makes it a second "SES US" row in the SCHWAB block, alongside the ordinary
# SES position - intentional, they are separate lots.
SYMBOL_OVERRIDES = {
    "SES+": "SES",
}

NUMBER_FORMATS = {
    "H": "#,##0.####;[Red]-#,##0.####;-",
    "K": "0.0000;[Red]-0.0000;-",
    "L": "yyyy-mm-dd",
}


def load_schwab_credentials():
    """Read the Schwab app key/secret from the process environment, falling back
    to ENV_FILE. Never hardcoded - this repo is public. Raises if not found, so a
    missing credential fails loudly instead of producing a confusing auth error."""
    app_key = os.environ.get(SCHWAB_KEY_VAR)
    app_secret = os.environ.get(SCHWAB_SECRET_VAR)

    if (not app_key or not app_secret) and os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{SCHWAB_KEY_VAR}=") and not app_key:
                    app_key = line.split("=", 1)[1].strip()
                elif line.startswith(f"{SCHWAB_SECRET_VAR}=") and not app_secret:
                    app_secret = line.split("=", 1)[1].strip()

    missing = [name for name, val in
               ((SCHWAB_KEY_VAR, app_key), (SCHWAB_SECRET_VAR, app_secret)) if not val]
    if missing:
        raise RuntimeError(
            f"Missing Schwab credential(s) {missing}. Set them in the environment "
            f"or add them to {ENV_FILE}.")
    return app_key, app_secret


def fetch_account_positions(client):
    """Return {nickname: (positions_list, cash_balance)} for every linked
    Schwab account that has a nickname mapped in NICKNAME_TO_PORTFOLIO."""
    prefs = client.preferences().json()
    nickname_by_account_number = {
        a["accountNumber"]: a["nickName"] for a in prefs.get("accounts", [])
    }

    linked = client.linked_accounts().json()
    result = {}
    for acct in linked:
        account_number = acct["accountNumber"]
        nickname = nickname_by_account_number.get(account_number)
        if nickname not in NICKNAME_TO_PORTFOLIO:
            continue
        details = client.account_details(acct["hashValue"], fields="positions").json()
        sa = details.get("securitiesAccount", {})
        positions = sa.get("positions", [])
        cash = sa.get("currentBalances", {}).get("cashBalance", 0.0)
        result[nickname] = (positions, cash)
    return result


def build_rows(portfolio_name, positions, cash, asof, skipped):
    """Translate one account's live positions into BBU row tuples:
    (portfolio, ticker_or_None, cusip_or_None, name, quantity, cost_price, asof, grouping)."""
    rows = []
    for p in positions:
        inst = p.get("instrument", {})
        symbol = inst.get("symbol")
        cusip = inst.get("cusip")
        desc = inst.get("description")
        asset_type = inst.get("assetType")

        if not symbol and not cusip:
            skipped.append((portfolio_name, p))
            continue

        qty = (p.get("longQuantity") or 0) - (p.get("shortQuantity") or 0)
        if asset_type == "FIXED_INCOME":
            qty *= 1000  # Schwab reports bond qty in $1000-face units; BBU wants face value

        cost_price = p.get("averagePrice") or 0

        use_cusip = cusip is not None and (symbol is None or symbol == cusip)
        if use_cusip:
            name = desc or cusip
            # Muni bond CUSIPs go in the FIRST SECURITY_ID column (C); every
            # other CUSIP-identified holding (e.g. the SCHWAB block's
            # equity/ETF CUSIPs) goes in column E. col_c/col_e are the two
            # SECURITY_ID cells replace_block() writes (columns C and E).
            # Per Arjun, 2026-07-22: muni bond id belongs in column C.
            if asset_type == "FIXED_INCOME":
                col_c, col_e = cusip, None
            else:
                col_c, col_e = None, cusip
        else:
            col_c, col_e = f"{SYMBOL_OVERRIDES.get(symbol, symbol)} US", None
            name = desc or symbol
        ticker, cusip_cell = col_c, col_e

        grouping = ASSET_TYPE_TO_GROUPING.get(asset_type, "Other")
        rows.append((portfolio_name, ticker, cusip_cell, name, qty, cost_price, asof, grouping))

    rows.append((portfolio_name, CASH_SECURITY_ID, None, "CASH", cash, 1, asof, "Portfolio Cash"))
    return rows


def find_block_range(ws, portfolio_names, start_row=1):
    """Find the contiguous [first_row, last_row] range (inclusive) covering
    all rows whose column-B portfolio name is in portfolio_names, starting
    the scan at start_row. Assumes those blocks are contiguous in the sheet."""
    first_row, last_row = None, None
    for row in range(start_row, ws.max_row + 1):
        value = ws.cell(row=row, column=2).value
        if value in portfolio_names:
            if first_row is None:
                first_row = row
            last_row = row
        elif first_row is not None:
            break
    return first_row, last_row


def replace_block(ws, portfolio_names, all_rows, start_row=1):
    """Delete the existing contiguous block for portfolio_names and insert
    freshly written rows in its place, shifting all following rows
    (subsequent blocks) down/up to match the new row count."""
    old_first, old_last = find_block_range(ws, portfolio_names, start_row)
    if old_first is None:
        raise RuntimeError(f"Could not locate existing portfolio block(s) {portfolio_names} in PRTU.xlsx")

    old_count = old_last - old_first + 1
    new_count = len(all_rows)

    ws.delete_rows(old_first, old_count)
    ws.insert_rows(old_first, new_count)

    for offset, row_tuple in enumerate(all_rows):
        portfolio, ticker, cusip_cell, name, qty, cost_price, asof, grouping = row_tuple
        r = old_first + offset
        ws.cell(row=r, column=2, value=portfolio)      # B: PORTFOLIO NAME
        ws.cell(row=r, column=3, value=ticker)          # C: SECURITY_ID (ticker)
        ws.cell(row=r, column=5, value=cusip_cell)       # E: SECURITY_ID (CUSIP)
        ws.cell(row=r, column=7, value=name)             # G: description
        h = ws.cell(row=r, column=8, value=qty)          # H: QUANTITY
        h.number_format = NUMBER_FORMATS["H"]
        k = ws.cell(row=r, column=11, value=cost_price)  # K: Cost Price
        k.number_format = NUMBER_FORMATS["K"]
        l = ws.cell(row=r, column=12, value=asof)        # L: As of Date
        l.number_format = NUMBER_FORMATS["L"]
        ws.cell(row=r, column=13, value=grouping)         # M: Custom grouping


def port_reachable(port, timeout=2):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            return True
    except OSError:
        return False


def fetch_ibkr_positions(port):
    """Pull IBKR positions/cash from one port via the ibkr_fetch_full.py subprocess.
    Returns (accounts_dict, paper_accounts) where accounts_dict maps
    account_number -> (positions, cash) and paper_accounts lists any
    "DU"/"DF"-prefixed (simulated) accounts found on this port."""
    result = subprocess.run(
        [IBKR_PYTHON, IBKR_FETCH_SCRIPT, "--port", str(port), "--client-id", str(IBKR_CLIENT_ID)],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"IBKR fetch failed (exit {result.returncode}): {result.stderr.strip()[-500:]}")

    items = json.loads(result.stdout)

    paper = sorted({i["account"] for i in items
                    if str(i["account"]).upper().startswith(IBKR_PAPER_ACCOUNT_PREFIXES)})

    positions_by_account = {}
    cash_by_account = {}
    for item in items:
        acct = item["account"]
        if item["sec_type"] == "CASH":
            cash_by_account[acct] = cash_by_account.get(acct, 0.0) + item["quantity"]
        else:
            positions_by_account.setdefault(acct, []).append(item)

    accounts = {
        acct: (positions_by_account.get(acct, []), cash_by_account.get(acct, 0.0))
        for acct in set(positions_by_account) | set(cash_by_account)
    }
    return accounts, paper


def fetch_ibkr_live():
    """Find the IBKR session serving the REAL accounts and return
    (port, accounts_dict), or (None, {}) if none is available.

    Probes every candidate port and decides live-vs-paper from the ACCOUNT
    PREFIX, not the port number (see IBKR_CANDIDATE_PORTS) - a port serving
    only simulated "DU"/"DF" accounts is rejected and the search continues, so
    paper holdings can never reach PRTU.xlsx.
    """
    for port in IBKR_CANDIDATE_PORTS:
        if not port_reachable(port):
            continue
        try:
            accounts, paper = fetch_ibkr_positions(port)
        except Exception as e:
            print(f"  IBKR port {port}: fetch failed ({e}) - trying next port")
            continue

        live = {a: v for a, v in accounts.items()
                if not str(a).upper().startswith(IBKR_PAPER_ACCOUNT_PREFIXES)}
        if paper and not live:
            print(f"  IBKR port {port}: PAPER account(s) {paper} - rejected, trying next port")
            continue
        if not live:
            print(f"  IBKR port {port}: no accounts returned - trying next port")
            continue
        if paper:
            print(f"  IBKR port {port}: ignoring paper account(s) {paper}")
        return port, live
    return None, {}


def build_futures_row(portfolio_name, item, asof, skipped):
    """Build one BBU row tuple for an IBKR FUT position, or return None (and
    record it in `skipped`) if it cannot be mapped to a verified Bloomberg
    ticker. Never guesses a ticker - a wrong futures ID points Bloomberg at
    the wrong contract.

    Bloomberg ticker = f"{bbg_root}{month_year} {sector}", where the root and
    sector come from IBKR_FUT_ROOT_TO_BBG (verified live) and the month+year
    code is taken verbatim from IBKR's localSymbol (e.g. M6AZ6 -> "Z6"). The
    quoted futures price = IBKR avgCost / multiplier (avgCost is per-contract
    cost basis for futures); BBU's cost-price column wants the price, per the
    template's own note ("for FX forwards, enter the forward rate").
    """
    root = item["symbol"]
    local_symbol = item.get("local_symbol") or ""
    mapping = IBKR_FUT_ROOT_TO_BBG.get(root)
    if mapping is None or not local_symbol.startswith(root):
        skipped.append((portfolio_name, item))
        return None

    bbg_root, sector = mapping
    month_year = local_symbol[len(root):]          # e.g. "Z6"
    try:
        multiplier = float(item.get("multiplier") or 0)
    except (TypeError, ValueError):
        multiplier = 0
    if not month_year or multiplier <= 0:
        skipped.append((portfolio_name, item))
        return None

    ticker = f"{bbg_root}{month_year} {sector}"
    qty = item["quantity"]                          # number of contracts, signed
    price = item["avg_price"] / multiplier          # per-unit quoted price
    name = f"{root} {local_symbol}"                 # keep IBKR identity for eyeballing
    return (portfolio_name, ticker, None, name, qty, price, asof, "Futures")


def build_ibkr_rows(portfolio_name, positions, cash, asof, skipped, non_usd):
    """Translate one IBKR account's live positions into BBU row tuples,
    matching the same tuple shape build_rows() produces for Schwab.

    - STK: Bloomberg exchange code comes from the trading currency via
      CURRENCY_TO_BBG_EXCHANGE, so non-USD holdings resolve on their local
      exchange (ETM/AUD -> "ETM AU", IES/GBP -> "IES LN"). An unmapped
      currency is skipped, never guessed.
    - FUT: mapped to a verified Bloomberg futures ticker (see
      build_futures_row / IBKR_FUT_ROOT_TO_BBG).
    - Anything else (options, etc.): skipped and reported.
    """
    rows = []
    for item in positions:
        sec_type = item["sec_type"]

        if sec_type == "FUT":
            fut_row = build_futures_row(portfolio_name, item, asof, skipped)
            if fut_row is not None:
                rows.append(fut_row)
            continue

        if sec_type != "STK":
            skipped.append((portfolio_name, item))
            continue

        symbol = item["symbol"]
        qty = item["quantity"]
        currency = item["currency"]
        exchange = CURRENCY_TO_BBG_EXCHANGE.get(currency)
        if exchange is None:
            skipped.append((portfolio_name, item))
            continue
        ticker = f"{SYMBOL_OVERRIDES.get(symbol, symbol)} {exchange}"
        if currency != "USD":
            non_usd.append((portfolio_name, item, ticker))

        cost_price = item["avg_price"]
        # Custom grouping stays "US Equities" for every IBKR stock, matching the
        # existing file's convention (it has no international-equity grouping).
        rows.append((portfolio_name, ticker, None, symbol, qty, cost_price, asof, "US Equities"))

    rows.append((portfolio_name, CASH_SECURITY_ID, None, "CASH", cash, 1, asof, "Portfolio Cash"))
    return rows


def main():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now()
    backup_path = os.path.join(
        BACKUP_DIR, f"PRTU_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}.xlsx"
    )
    shutil.copy2(PRTU_PATH, backup_path)
    print(f"Backed up existing PRTU.xlsx -> {backup_path}")

    app_key, app_secret = load_schwab_credentials()
    client = schwabdev.Client(app_key, app_secret)

    account_data = fetch_account_positions(client)

    missing = set(NICKNAME_TO_PORTFOLIO) - set(account_data)
    if missing:
        print(f"WARNING: expected Schwab accounts not found/linked: {sorted(missing)}")

    skipped = []
    rows_by_portfolio = {}
    for nickname, (positions, cash) in account_data.items():
        portfolio_name = NICKNAME_TO_PORTFOLIO[nickname]
        rows_by_portfolio[portfolio_name] = build_rows(
            portfolio_name, positions, cash, timestamp, skipped
        )

    schwab_rows = []
    for portfolio_name in PORTFOLIO_ORDER:
        if portfolio_name in rows_by_portfolio:
            schwab_rows.extend(rows_by_portfolio[portfolio_name])
        else:
            print(f"WARNING: no live data for portfolio block '{portfolio_name}' - left out of rebuild")

    # --- IBKR ---
    ibkr_rows_by_portfolio = {}
    ibkr_skipped = []
    ibkr_non_usd = []
    print("\nIBKR: locating the session serving the real accounts...")
    ibkr_port, ibkr_data = fetch_ibkr_live()
    if ibkr_port is None:
        print(f"WARNING: no LIVE IBKR session found (probed {IBKR_CANDIDATE_PORTS}) - "
              f"IBKR blocks left untouched. Start/log in to live TWS or IB Gateway.")
    else:
        print(f"IBKR: using port {ibkr_port}, live accounts {sorted(ibkr_data)}")

        missing_ibkr = set(IBKR_ACCOUNT_TO_PORTFOLIO) - set(ibkr_data)
        if missing_ibkr:
            print(f"WARNING: expected IBKR accounts not visible: {sorted(missing_ibkr)}")

        for account_number, (positions, cash) in ibkr_data.items():
            if account_number == "All":  # accountSummary aggregate row, not a real account
                continue
            portfolio_name = IBKR_ACCOUNT_TO_PORTFOLIO.get(account_number)
            if portfolio_name is None:
                print(f"WARNING: IBKR account {account_number} has no mapped PRTU block - skipped entirely")
                continue
            ibkr_rows_by_portfolio[portfolio_name] = build_ibkr_rows(
                portfolio_name, positions, cash, timestamp, ibkr_skipped, ibkr_non_usd
            )

    wb = openpyxl.load_workbook(PRTU_PATH)
    ws = wb["Book1"]
    replace_block(ws, set(PORTFOLIO_ORDER), schwab_rows, start_row=1)
    for portfolio_name, rows in ibkr_rows_by_portfolio.items():
        replace_block(ws, {portfolio_name}, rows, start_row=1)
    wb.save(PRTU_PATH)

    print(f"\nUpdated {sum(len(v) for v in rows_by_portfolio.values())} Schwab rows across "
          f"{len(rows_by_portfolio)} portfolio blocks in {PRTU_PATH}")
    for portfolio_name in PORTFOLIO_ORDER:
        n = len(rows_by_portfolio.get(portfolio_name, []))
        print(f"  {portfolio_name}: {n} rows")

    if ibkr_rows_by_portfolio:
        print(f"\nUpdated {sum(len(v) for v in ibkr_rows_by_portfolio.values())} IBKR rows across "
              f"{len(ibkr_rows_by_portfolio)} portfolio block(s):")
        for portfolio_name, rows in ibkr_rows_by_portfolio.items():
            print(f"  {portfolio_name}: {len(rows)} rows")

    if skipped:
        print(f"\nWARNING: skipped {len(skipped)} Schwab position(s) with no usable symbol or CUSIP "
              f"(not written to PRTU.xlsx - review manually in Schwab):")
        for portfolio_name, p in skipped:
            print(f"  [{portfolio_name}] {p}")

    if ibkr_skipped:
        print(f"\nWARNING: skipped {len(ibkr_skipped)} IBKR position(s) - an option/other "
              f"instrument, a stock currency not in CURRENCY_TO_BBG_EXCHANGE, or a future "
              f"whose root is not in IBKR_FUT_ROOT_TO_BBG (review manually, add a mapping):")
        for portfolio_name, item in ibkr_skipped:
            extra = f" local={item.get('local_symbol')}" if item.get("sec_type") == "FUT" else ""
            print(f"  [{portfolio_name}] {item['symbol']} ({item['sec_type']}/{item['currency']}) qty={item['quantity']}{extra}")

    if ibkr_non_usd:
        print(f"\nNOTE: {len(ibkr_non_usd)} non-USD IBKR holding(s) written to their local exchange:")
        for portfolio_name, item, ticker in ibkr_non_usd:
            print(f"  [{portfolio_name}] {item['symbol']} ({item['currency']}) -> '{ticker}'")


if __name__ == "__main__":
    main()

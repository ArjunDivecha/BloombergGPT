"""
=============================================================================
SCRIPT NAME: ArjunBloomberg.py
=============================================================================

INPUT FILES:
- /Users/arjundivecha/Dropbox/AAA Backup/A Working/BloombergGPT/PRTU.xlsx
  Existing Bloomberg BBU portfolio-upload template. Sheet "Book1" contains
  one contiguous row-block per portfolio (PORTFOLIO NAME in column B).
  Live data (none) - all position data below comes from the Schwab API.

- /Users/arjundivecha/Dropbox/AAA Backup/A Working/News/report/ibkr_fetch.py
  Existing, already-working IBKR position-fetch script from the News
  project. Invoked as a subprocess under News' own .venv-ibkr312
  interpreter (ib_insync requires Python 3.12) against a locally running,
  logged-in IB Gateway/TWS session on 127.0.0.1:4002. Not modified.

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
All 3 IBKR accounts are visible on the LIVE TWS API port (7496) and map
1:1 to the three IBKR blocks. Verified 2026-07-22: each account's live
holdings matched that block's existing hand-maintained holdings exactly.

    IBKR account -> PRTU portfolio block
    U1399611      -> IBKRMAIN         (CEE, INTC, CORD, SCHW, COPX, ...)
    U14983106     -> IBKREXPERIMENT   (XBI, XLY, KRE, XLC, IHI, KBE)
    U24887919     -> IBKRLONGSHORT    (no positions, cash only)

IMPORTANT - live vs paper ports: port 4002 (and 7497) are IBKR's PAPER
trading ports and expose a single simulated "DU..."-prefixed account whose
holdings are unrelated to the real portfolios. Connecting there and writing
the result into PRTU.xlsx silently corrupts the real blocks (this happened
on 2026-07-22 before the mapping was verified). This script therefore only
probes LIVE ports (see IBKR_LIVE_PORTS) and additionally hard-fails if any
returned account is paper-prefixed.

Each IBKR position becomes a BBU row the same way as Schwab positions:
    - Only sec_type == "STK" positions are written; options/futures are
      skipped with a warning rather than guessing a Bloomberg identifier
      IBKR's position response doesn't reliably give us.
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
- LIVE TWS or IB Gateway must be running and logged in on 127.0.0.1:7496
  or :4001. If neither is reachable, the IBKR portion is skipped with a
  warning and the IBKR blocks are left untouched (Schwab blocks still
  update normally). Paper-trading ports are never used - see IBKR SECTION.
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

# IBKR access, reusing the News project's proven fetch script/venv
IBKR_PYTHON = "/Users/arjundivecha/Dropbox/AAA Backup/A Working/News/.venv-ibkr312/bin/python3"
IBKR_FETCH_SCRIPT = "/Users/arjundivecha/Dropbox/AAA Backup/A Working/News/report/ibkr_fetch.py"

# LIVE IBKR API ports only, tried in order: TWS-live (7496), Gateway-live (4001).
# The PAPER ports (TWS 7497, Gateway 4002) are deliberately EXCLUDED - connecting
# to paper returns a simulated "DU..."-prefixed account whose holdings would
# silently overwrite the real portfolio blocks in PRTU.xlsx. This bit us on
# 2026-07-22 (paper account DUR170932 on 4002 looked like a real pull), hence
# both the port allowlist and the is-paper account guard in fetch_ibkr_positions().
IBKR_LIVE_PORTS = [7496, 4001]
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
# Confirmed 2026-07-22 against live TWS (port 7496): each account's live
# holdings matched the corresponding block's existing holdings exactly.
IBKR_ACCOUNT_TO_PORTFOLIO = {
    "U1399611": "IBKRMAIN",
    "U14983106": "IBKREXPERIMENT",
    "U24887919": "IBKRLONGSHORT",
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


def find_live_ibkr_port():
    """Return the first reachable LIVE IBKR API port, or None. Paper ports are
    never probed - see IBKR_LIVE_PORTS."""
    for port in IBKR_LIVE_PORTS:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=2):
                return port
        except OSError:
            continue
    return None


def fetch_ibkr_positions(port):
    """Pull live IBKR positions/cash via News' proven ibkr_fetch.py subprocess.
    Returns {account_number: (positions, cash)} where positions is a list of
    the raw dicts ibkr_fetch.py emits (symbol/sec_type/currency/quantity/avg_price)."""
    result = subprocess.run(
        [IBKR_PYTHON, IBKR_FETCH_SCRIPT, "--port", str(port), "--client-id", str(IBKR_CLIENT_ID)],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"IBKR fetch failed (exit {result.returncode}): {result.stderr.strip()[-500:]}")

    items = json.loads(result.stdout)

    # Guard: refuse to write simulated paper-trading data into the real
    # portfolio file. IBKR paper accounts are "DU"/"DF"-prefixed.
    paper = sorted({i["account"] for i in items if str(i["account"]).upper().startswith(("DU", "DF"))})
    if paper:
        raise RuntimeError(
            f"Refusing to use IBKR paper-trading account(s) {paper} on port {port}. "
            f"Log in to LIVE TWS/Gateway instead.")
    positions_by_account = {}
    cash_by_account = {}
    for item in items:
        acct = item["account"]
        if item["sec_type"] == "CASH":
            cash_by_account[acct] = cash_by_account.get(acct, 0.0) + item["quantity"]
        else:
            positions_by_account.setdefault(acct, []).append(item)

    return {
        acct: (positions_by_account.get(acct, []), cash_by_account.get(acct, 0.0))
        for acct in set(positions_by_account) | set(cash_by_account)
    }


def build_ibkr_rows(portfolio_name, positions, cash, asof, skipped, non_usd):
    """Translate one IBKR account's live positions into BBU row tuples,
    matching the same tuple shape build_rows() produces for Schwab.

    Non-stock instruments (options/futures) are skipped - IBKR's position
    response has no reliable Bloomberg identifier for them.

    Each stock's Bloomberg exchange code comes from its trading currency via
    CURRENCY_TO_BBG_EXCHANGE, so non-USD holdings resolve on their local
    exchange (ETM/AUD -> "ETM AU", IES/GBP -> "IES LN") rather than being
    mislabelled " US". An unmapped currency is skipped, never guessed.
    """
    rows = []
    for item in positions:
        symbol = item["symbol"]
        qty = item["quantity"]
        currency = item["currency"]
        if item["sec_type"] != "STK":
            skipped.append((portfolio_name, item))
            continue

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
    ibkr_port = find_live_ibkr_port()
    if ibkr_port is None:
        print(f"\nWARNING: no LIVE IBKR API port reachable (tried {IBKR_LIVE_PORTS}) - "
              f"IBKR blocks left untouched. Start/log in to live TWS or IB Gateway.")
    else:
        print(f"\nIBKR: using live port {ibkr_port}")
        try:
            ibkr_data = fetch_ibkr_positions(ibkr_port)
        except Exception as e:
            print(f"WARNING: IBKR fetch failed ({e}) - IBKR blocks left untouched")
            ibkr_data = {}

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
        print(f"\nWARNING: skipped {len(ibkr_skipped)} IBKR position(s) - non-stock, or a "
              f"currency with no Bloomberg exchange code mapped in "
              f"CURRENCY_TO_BBG_EXCHANGE (review manually):")
        for portfolio_name, item in ibkr_skipped:
            print(f"  [{portfolio_name}] {item['symbol']} ({item['sec_type']}/{item['currency']}) qty={item['quantity']}")

    if ibkr_non_usd:
        print(f"\nNOTE: {len(ibkr_non_usd)} non-USD IBKR holding(s) written to their local exchange:")
        for portfolio_name, item, ticker in ibkr_non_usd:
            print(f"  [{portfolio_name}] {item['symbol']} ({item['currency']}) -> '{ticker}'")


if __name__ == "__main__":
    main()

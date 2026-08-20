#!/usr/bin/env python3
"""
=============================================================================
SCRIPT NAME: ibkr_fetch_full.py
=============================================================================

INPUT FILES:
    (none - connects to a live, logged-in IB Gateway/TWS on 127.0.0.1)

OUTPUT FILES:
    (stdout only - a JSON array of position dicts)

VERSION: 1.0
LAST UPDATED: 2026-07-28
AUTHOR: Assistant (for Arjun Divecha)

DESCRIPTION:
    Fetches all Interactive Brokers portfolio positions and cash balances and
    prints them as JSON to stdout. This is a superset of the News project's
    report/ibkr_fetch.py: in addition to symbol/sec_type/currency/quantity/
    avg_cost it also emits, for every position, the fields needed to build a
    Bloomberg FUTURES ticker downstream - local_symbol, expiry, multiplier,
    and exchange. ArjunBloomberg.py consumes this to populate the IBKR
    portfolio blocks in PRTU.xlsx, including futures.

    Why a separate script (rather than editing News' ibkr_fetch.py): News'
    version is shared with that project and only needs the basic fields;
    this one is owned by the BloombergGPT project so the futures-detail
    fields can be added without touching News.

    Run BY ArjunBloomberg.py as a subprocess under News' .venv-ibkr312
    interpreter. Everything except
    the JSON payload goes to stderr.

    Exit codes: 0 = success, 2 = connection failed, 3 = no data.

    avg_cost semantics (IMPORTANT for the downstream cost-price column):
      - STK: IBKR avgCost is the average price per share -> use as-is.
      - FUT: IBKR avgCost is the per-contract cost basis = price * multiplier;
        divide by `multiplier` downstream to recover the quoted futures price.

DEPENDENCIES:
    - ibkr_connect (brings ib_async)
      pip install -e "/Users/arjundivecha/Dropbox/AAA Backup/A Working/IBKR API"

USAGE:
    "/Users/arjundivecha/Dropbox/AAA Backup/A Working/News/.venv-ibkr312/bin/python3" \
        ibkr_fetch_full.py
=============================================================================
"""

import argparse
import json
import sys


def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    # --port/--client-id removed 2026-08-19 (IBKR consolidation). These are REAL
    # holdings, so ibkr_connect's `portfolio` lane is the only correct source:
    # the LIVE gateway on 4001, read-only, with this repo's registered clientId.
    # It also proves the gateway is actually serving account data before handing
    # the connection over -- a gateway that is logged in but not serving account
    # data makes reqPositions() hang forever rather than fail.
    from ibkr_connect import LiveGatewayNeedsLogin, open_portfolio
    from ibkr_connect.compat import util

    try:
        ib = open_portfolio("bloomberggpt")
    except LiveGatewayNeedsLogin as e:
        print(f"IBKR live gateway unavailable: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"IBKR connection failed: {e}", file=sys.stderr)
        sys.exit(2)

    try:
        accounts = ib.managedAccounts()
        print(f"IBKR accounts: {accounts}", file=sys.stderr)

        # Bounded: reqPositions() has no timeout of its own.
        try:
            positions = util.run(ib.reqPositionsAsync(), timeout=60.0)
        except Exception as e:
            print(f"IBKR: positions did not return within 60s ({type(e).__name__}). "
                  f"Diagnose with: python3 -m ibkr_connect.doctor", file=sys.stderr)
            sys.exit(2)
        print(f"IBKR positions: {len(positions)}", file=sys.stderr)

        rows = []
        for p in positions:
            if not p.position:
                continue
            c = p.contract
            rows.append({
                "account": p.account,
                "symbol": c.symbol,
                "sec_type": c.secType,
                "currency": c.currency,
                "quantity": float(p.position),
                "avg_price": float(p.avgCost),      # see avg_cost semantics in header
                # extra fields for futures ticker construction (blank/None for STK)
                "local_symbol": c.localSymbol or "",
                "expiry": c.lastTradeDateOrContractMonth or "",
                "multiplier": c.multiplier or "",
                "exchange": c.exchange or "",
            })

        # Cash balances per account via one-shot account summary
        summary = ib.accountSummary()
        for av in summary:
            if av.tag == "TotalCashValue" and av.currency == "USD":
                rows.append({
                    "account": av.account,
                    "symbol": "CASH",
                    "sec_type": "CASH",
                    "currency": "USD",
                    "quantity": float(av.value),
                    "avg_price": 1.0,
                    "local_symbol": "",
                    "expiry": "",
                    "multiplier": "",
                    "exchange": "",
                })

        if not rows:
            print("IBKR returned no positions", file=sys.stderr)
            sys.exit(3)

        print(json.dumps(rows))
    finally:
        if ib.isConnected():
            ib.disconnect()


if __name__ == "__main__":
    main()

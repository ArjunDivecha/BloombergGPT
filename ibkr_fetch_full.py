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
    interpreter, because ib_insync requires Python 3.12. Everything except
    the JSON payload goes to stderr.

    Exit codes: 0 = success, 2 = connection failed, 3 = no data.

    avg_cost semantics (IMPORTANT for the downstream cost-price column):
      - STK: IBKR avgCost is the average price per share -> use as-is.
      - FUT: IBKR avgCost is the per-contract cost basis = price * multiplier;
        divide by `multiplier` downstream to recover the quoted futures price.

DEPENDENCIES:
    - ib_insync (Python 3.12 venv only: News/.venv-ibkr312)

USAGE:
    "/Users/arjundivecha/Dropbox/AAA Backup/A Working/News/.venv-ibkr312/bin/python3" \
        ibkr_fetch_full.py [--port 4001] [--client-id 233]
=============================================================================
"""

import argparse
import json
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=4001)
    parser.add_argument("--client-id", type=int, default=233)
    args = parser.parse_args()

    from ib_insync import IB

    ib = IB()
    try:
        ib.connect("127.0.0.1", args.port,
                   clientId=args.client_id, readonly=True, timeout=20)
    except Exception as e:
        print(f"IBKR connection failed: {e}", file=sys.stderr)
        sys.exit(2)

    try:
        accounts = ib.managedAccounts()
        print(f"IBKR accounts: {accounts}", file=sys.stderr)

        positions = ib.reqPositions()
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

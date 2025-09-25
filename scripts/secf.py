"""
SECF-style Security Finder (//blp/instruments)

Examples
- python scripts/secf.py "BALTIC* INDEX*" --max 1000
- python scripts/secf.py "OMX Baltic*" --max 200

This script sends an instrumentListRequest to //blp/instruments and prints a
ranked (by security) list of matching securities similar to Bloomberg SECF.

Notes
- Requires: Bloomberg Terminal running and blpapi installed.
- Supports wildcard patterns in the query (e.g., BALTIC* INDEX*).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import List

import blpapi
from blpapi import SessionOptions, Session, Event


@dataclass
class InstrumentRow:
    security: str
    description: str
    yellow_key: str


def start_session(host: str = "localhost", port: int = 8194) -> Session:
    opts = SessionOptions()
    opts.setServerHost(host)
    opts.setServerPort(port)
    session = Session(opts)
    if not session.start():
        raise SystemExit("Failed to start Bloomberg session")
    if not session.openService("//blp/instruments"):
        session.stop()
        raise SystemExit("Failed to open //blp/instruments")
    return session


def instrument_search(query: str, max_results: int, host: str, port: int) -> List[InstrumentRow]:
    session = start_session(host, port)
    results: List[InstrumentRow] = []
    try:
        service = session.getService("//blp/instruments")
        request = service.createRequest("instrumentListRequest")
        request.set("query", query)
        request.set("maxResults", int(max_results))

        session.sendRequest(request)

        while True:
            event = session.nextEvent(5000)
            et = event.eventType()
            if et in (Event.PARTIAL_RESPONSE, Event.RESPONSE):
                for msg in event:
                    if msg.hasElement("responseError"):
                        err = msg.getElement("responseError")
                        raise SystemExit(f"Response error: {err}")

                    # Older schema uses instrumentListResponse; newer adds results array
                    if msg.hasElement("instrumentListResponse"):
                        container = msg.getElement("instrumentListResponse")
                    elif msg.hasElement("results"):
                        container = msg.getElement("results")
                    else:
                        continue

                    for i in range(container.numValues()):
                        row = container.getValueAsElement(i)
                        sec = row.getElementAsString("security") if row.hasElement("security") else ""
                        desc = row.getElementAsString("description") if row.hasElement("description") else ""
                        yk = row.getElementAsString("yellowKey") if row.hasElement("yellowKey") else ""
                        if sec or desc:
                            results.append(InstrumentRow(sec, desc, yk))
                if et == Event.RESPONSE:
                    break
            elif et == Event.TIMEOUT:
                break
    finally:
        session.stop()

    # De-duplicate while preserving first occurrence
    seen = set()
    deduped: List[InstrumentRow] = []
    for r in results:
        key = (r.security, r.description, r.yellow_key)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)

    deduped.sort(key=lambda r: (r.security or ""))
    return deduped


def main() -> None:
    p = argparse.ArgumentParser(description="SECF-style security search via //blp/instruments")
    p.add_argument("query", help="Search pattern, e.g., 'BALTIC* INDEX*'")
    p.add_argument("--max", type=int, default=15, help="Maximum results to request (default 15)")
    p.add_argument("--host", default="localhost", help="Bloomberg host (default localhost)")
    p.add_argument("--port", type=int, default=8194, help="Bloomberg port (default 8194)")
    p.add_argument("--json", action="store_true", help="Output JSON instead of table")
    args = p.parse_args()

    rows = instrument_search(args.query, args.max, args.host, args.port)

    if args.json:
        import json
        print(json.dumps([r.__dict__ for r in rows], ensure_ascii=False, indent=2))
        return

    print(f"Query: {args.query}")
    print(f"Found {len(rows)} instruments")
    print("-" * 120)
    print(f"{'Security':<20} {'Yellow':<10} Description")
    print("-" * 120)
    for r in rows[: args.max]:
        print(f"{r.security:<20} {r.yellow_key:<10} {r.description}")


if __name__ == "__main__":
    main()

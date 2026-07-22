"""
=============================================================================
SCRIPT NAME: list_instrument_ops.py
=============================================================================

DESCRIPTION:
    Connects to Bloomberg via the blpapi library, opens the
    //blp/instruments service, enumerates every operation available on
    that service, and prints each operation name to stdout.  No data
    is saved or read from disk — the script is purely diagnostic,
    intended to discover what instrument operations (e.g., instrument
    list requests, security lookup) the Bloomberg API exposes.

INPUT FILES:
    (none — this script communicates only with the Bloomberg API)

OUTPUT FILES:
    (none — this script only prints to stdout)

VERSION: 1.0
LAST UPDATED: 2026-06-05
AUTHOR: Arjun Divecha

DEPENDENCIES:
    - blpapi

USAGE:
    python list_instrument_ops.py

NOTES:
    - Bloomberg Terminal must be running and logged in on the same
      machine (bbcomm on localhost:8194).
    - The //blp/instruments service provides functions such as
      instrumentListRequest for searching securities.
=============================================================================
"""
import blpapi
from blpapi import SessionOptions, Session

options = SessionOptions(); options.setServerHost('localhost'); options.setServerPort(8194)
session = Session(options)
if not session.start(): raise SystemExit('start failed')
if not session.openService('//blp/instruments'): raise SystemExit('open service failed')
service = session.getService('//blp/instruments')
print('Operations:')
for i in range(service.numOperations()):
    op = service.getOperation(i)
    print('-', op.name())
session.stop()

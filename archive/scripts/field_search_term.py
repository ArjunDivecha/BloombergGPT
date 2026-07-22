"""
=============================================================================
SCRIPT NAME: field_search_term.py
=============================================================================

DESCRIPTION:
    Searches the Bloomberg field database for fields matching a given search
    term via the Bloomberg API (blpapi). Connects to a local Bloomberg
    session on localhost:8194, sends a FieldSearchRequest with the user-
    provided search term (defaults to "CPI"), and retrieves each matching
    field's mnemonic, description, datatype, and category name. Results are
    printed to stdout; only the first 10 matching records are displayed in
    detail along with the total count.

INPUT FILES:
    (none — this script reads a search term from the command line and queries
     the Bloomberg API; no local input files are used)

OUTPUT FILES:
    (none — results are printed to stdout only; no files are written)

VERSION: 1.0
LAST UPDATED: 2026-06-05
AUTHOR: Arjun Divecha

DEPENDENCIES:
    - blpapi (Bloomberg Python API)

USAGE:
    python field_search_term.py [search_term]

NOTES:
    - Requires a running Bloomberg Terminal with bbcomm on localhost:8194.
    - If no search term is provided as a command-line argument, defaults to "CPI".
    - Only first 10 records are printed in full; the total count is shown.
=============================================================================
"""
import sys
import blpapi
from blpapi import SessionOptions, Session

term = sys.argv[1] if len(sys.argv) > 1 else 'CPI'

options = SessionOptions(); options.setServerHost('localhost'); options.setServerPort(8194)
session = Session(options)
if not session.start():
    raise SystemExit('start failed')
if not session.openService('//blp/apiflds'):
    raise SystemExit('open service failed')
service = session.getService('//blp/apiflds')
request = service.createRequest('FieldSearchRequest')
request.set('searchSpec', term)

session.sendRequest(request)
records = []
while True:
    event = session.nextEvent(500)
    for message in event:
        if message.hasElement('fieldData'):
            data = message.getElement('fieldData')
            for entry in data.values():
                info = entry.getElement('fieldInfo')
                category = ''
                if info.hasElement('categoryName'):
                    cat_elem = info.getElement('categoryName')
                    category = ', '.join(cat_elem.values()) if cat_elem.numValues() else ''
                records.append({
                    'mnemonic': info.getElementAsString('mnemonic'),
                    'description': info.getElementAsString('description'),
                    'datatype': info.getElementAsString('datatype'),
                    'category': category,
                })
    if event.eventType() == blpapi.Event.RESPONSE:
        break
session.stop()
print(f"Search term '{term}' -> {len(records)} records")
for rec in records[:10]:
    print(rec)

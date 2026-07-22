"""
=================================================================================================
SCRIPT NAME: instrument_search.py
=================================================================================================

DESCRIPTION:
    Connects to the Bloomberg Terminal API (blpapi), sends an instrument
    search request for a given query string (defaults to 'India CPI'), and
    prints the matching instruments to stdout. The search filters results to
    economic indicators (yellowKey = 'ECON') and limits output to 100 results.
    This is useful for finding Bloomberg instrument identifiers (tickers) by
    name or description before pulling price or reference data.

INPUT FILES:
    (none -- this script reads a query string from the command line and
     connects to Bloomberg over the network)

OUTPUT FILES:
    (none -- this script only prints results to stdout)

VERSION: 1.0
LAST UPDATED: 2026-06-05
AUTHOR: Arjun Divecha

DEPENDENCIES:
    - blpapi (Bloomberg Professional API Python SDK)

USAGE:
    python instrument_search.py <query>

NOTES:
    - Requires Bloomberg Terminal to be running and accessible on localhost:8194.
    - The yellowKeyFilter is set to 'ECON' to narrow results to economic
      indicators; change this to 'EQUITY', 'CORP', etc. to search other types.
    - If no query is provided as a command-line argument, defaults to 'India CPI'.
=================================================================================================
"""

import sys
import blpapi
from blpapi import SessionOptions, Session, exception

query = sys.argv[1] if len(sys.argv) > 1 else 'India CPI'
options = SessionOptions(); options.setServerHost('localhost'); options.setServerPort(8194)
session = Session(options)
if not session.start():
    raise SystemExit('start failed')
if not session.openService('//blp/instruments'):
    raise SystemExit('open service failed')
service = session.getService('//blp/instruments')
request = service.createRequest('instrumentListRequest')
request.set('query', query)
try:
    request.set('maxResults', 100)
except exception.NotFoundException:
    pass
req_element = request.asElement()
try:
    yellow_filter = req_element.getElement('yellowKeyFilter')
except exception.NotFoundException:
    yellow_filter = req_element.appendElement('yellowKeyFilter') if req_element.isArray() or req_element.datatype() else None

if yellow_filter is not None:
    try:
        yellow_filter.appendValue('ECON')
    except Exception:
        pass

session.sendRequest(request)
results = []
while True:
    event = session.nextEvent(500)
    for message in event:
        if message.hasElement('instrumentListResponse'):
            data = message.getElement('instrumentListResponse')
            for instrument in data.values():
                entry = {'security': instrument.getElementAsString('security'), 'description': instrument.getElementAsString('description')}
                if instrument.hasElement('yellowKey'):
                    entry['yellowKey'] = instrument.getElementAsString('yellowKey')
                results.append(entry)
    if event.eventType() == blpapi.Event.RESPONSE:
        break
session.stop()
print(f"Query '{query}' -> {len(results)} instruments")
for rec in results:
    print(rec)

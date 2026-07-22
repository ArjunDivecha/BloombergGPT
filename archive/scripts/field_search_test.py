"""
=============================================================================
SCRIPT NAME: field_search_test.py
=============================================================================

DESCRIPTION:
    Connects to a Bloomberg terminal session via the bbg API and performs a
    field search against the //blp/apiflds service using the query string
    "CPI". For each matching field returned, it extracts the mnemonic,
    description, and field type, then prints the count of results and the
    first 10 matches to stdout. This is a utility for discovering available
    Bloomberg field identifiers related to a topic.

INPUT FILES:
    (none — this script generates its own data via Bloomberg API)

OUTPUT FILES:
    (none — this script only prints to stdout)

VERSION: 1.0
LAST UPDATED: 2026-06-05
AUTHOR: Arjun Divecha

DEPENDENCIES:
    - blpapi (Bloomberg Python API)

USAGE:
    python field_search_test.py

NOTES:
    - Requires a running Bloomberg Terminal session (Parallels VM) with bbcomm
      exposed on localhost:8194.
    - The script connects to //blp/apiflds, so no Bloomberg data license is
      needed — this is a metadata/field-discovery service.
=============================================================================
"""

import blpapi
from blpapi import SessionOptions, Session

options = SessionOptions()
options.setServerHost('localhost')
options.setServerPort(8194)

session = Session(options)
if not session.start():
    raise SystemExit('start failed')
if not session.openService('//blp/apiflds'):
    raise SystemExit('open service failed')
service = session.getService('//blp/apiflds')
request = service.createRequest('FieldSearchRequest')
request.set('searchSpec', 'CPI')

session.sendRequest(request)
results = []
while True:
    event = session.nextEvent(500)
    for message in event:
        if message.hasElement('fieldData'):
            data = message.getElement('fieldData')
            for field in data.values():
                results.append(
                    (
                        field.getElementAsString('mnemonic'),
                        field.getElementAsString('description'),
                        field.getElementAsString('fieldType') if field.hasElement('fieldType') else '',
                    )
                )
    if event.eventType() == blpapi.Event.RESPONSE:
        break
session.stop()
print(len(results))
print('\n'.join(f"{mnemonic}: {desc} [{ftype}]" for mnemonic, desc, ftype in results[:10]))

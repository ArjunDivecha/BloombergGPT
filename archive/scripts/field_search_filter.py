import blpapi
from blpapi import SessionOptions, Session

SEARCH_TERM = 'India'
FIELD_SEARCH_TOKEN = 'CPI'

options = SessionOptions(); options.setServerHost('localhost'); options.setServerPort(8194)
session = Session(options)
if not session.start():
    raise SystemExit('start failed')
if not session.openService('//blp/apiflds'):
    raise SystemExit('open apiflds failed')
service = session.getService('//blp/apiflds')

# Step 1: broad search to get CPI-related fields
search_request = service.createRequest('FieldSearchRequest')
search_request.set('searchSpec', FIELD_SEARCH_TOKEN)
session.sendRequest(search_request)
all_fields = []
while True:
    event = session.nextEvent(500)
    for message in event:
        if message.hasElement('fieldData'):
            data = message.getElement('fieldData')
            for entry in data.values():
                info = entry.getElement('fieldInfo')
                all_fields.append(info.getElementAsString('mnemonic'))
    if event.eventType() == blpapi.Event.RESPONSE:
        break

print(f"Retrieved {len(all_fields)} CPI-related fields")

# Step 2: fetch field info in batches and filter documentation for SEARCH_TERM
matches = []
BATCH = 25
for i in range(0, len(all_fields), BATCH):
    subset = all_fields[i:i+BATCH]
    info_request = service.createRequest('FieldInfoRequest')
    for mnemonic in subset:
        info_request.append('id', mnemonic)
    session.sendRequest(info_request)
    while True:
        event = session.nextEvent(500)
        for message in event:
            if message.hasElement('fieldData'):
                data = message.getElement('fieldData')
                for entry in data.values():
                    info = entry.getElement('fieldInfo')
                    doc = info.getElementAsString('documentation') if info.hasElement('documentation') else ''
                    if SEARCH_TERM.lower() in doc.lower():
                        matches.append(
                            {
                                'mnemonic': info.getElementAsString('mnemonic'),
                                'description': info.getElementAsString('description'),
                                'documentation': doc[:200],
                            }
                        )
        if event.eventType() == blpapi.Event.RESPONSE:
            break

if not matches:
    print(f"No CPI fields mention '{SEARCH_TERM}' in their documentation")
else:
    print(f"Fields mentioning '{SEARCH_TERM}': {len(matches)}")
    for match in matches:
        print(f"{match['mnemonic']}: {match['description']}")
        print(f"Doc snippet: {match['documentation']}")

session.stop()

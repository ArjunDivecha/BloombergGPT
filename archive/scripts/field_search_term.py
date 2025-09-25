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

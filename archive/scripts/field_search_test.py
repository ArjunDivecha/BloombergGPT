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

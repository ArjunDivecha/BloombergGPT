import blpapi
from blpapi import SessionOptions, Session

options = SessionOptions(); options.setServerHost('localhost'); options.setServerPort(8194)
session = Session(options)
if not session.start(): raise SystemExit('start failed')
if not session.openService('//blp/apiflds'): raise SystemExit('open service failed')
service = session.getService('//blp/apiflds')
request = service.createRequest('FieldSearchRequest')
request.set('searchSpec', 'CPI')
session.sendRequest(request)
while True:
    event = session.nextEvent(500)
    for message in event:
        print('Event type:', event.eventType())
        print(message)
    if event.eventType() == blpapi.Event.RESPONSE:
        break
session.stop()

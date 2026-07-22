import blpapi
from blpapi import SessionOptions, Session

options = SessionOptions(); options.setServerHost('localhost'); options.setServerPort(8194)
session = Session(options)
if not session.start():
    raise SystemExit('start failed')
if not session.openService('//blp/refdata'):
    raise SystemExit('open refdata failed')
service = session.getService('//blp/refdata')
request = service.createRequest('HistoricalDataRequest')
request.append('securities', 'INCPYOY Index')
request.append('fields', 'PX_LAST')
request.set('startDate', '20240101')
request.set('endDate', '20240301')
request.set('periodicitySelection', 'MONTHLY')
session.sendRequest(request)
while True:
    event = session.nextEvent(500)
    for message in event:
        print(message)
    if event.eventType() == blpapi.Event.RESPONSE:
        break
session.stop()

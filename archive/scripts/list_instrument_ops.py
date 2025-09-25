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

import blpapi
from blpapi import SessionOptions, Session

options = SessionOptions(); options.setServerHost('localhost'); options.setServerPort(8194)
session = Session(options)
if not session.start():
    raise SystemExit('start failed')
if not session.openService('//blp/apiflds'):
    raise SystemExit('open service failed')
service = session.getService('//blp/apiflds')
defn = service.getRequestDefinition('FieldSearchRequest')
def print_def(n, indent=0):
    pad = ' ' * indent
    print(f"{pad}- {n.name()} ({n.datatype()}) optional={n.isOptional()}")
    if n.datatype() == blpapi.Schema.Datatype.CHOICE or n.type() == blpapi.SchemaElementDefinition.Type.SEQUENCE:
        for child in n.elements():
            print_def(child, indent + 2)
    else:
        for child in n.elements():
            print_def(child, indent + 2)

print_def(defn)
session.stop()

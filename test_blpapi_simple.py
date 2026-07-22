"""
=============================================================================
SCRIPT NAME: test_blpapi_simple.py
=============================================================================

DESCRIPTION:
    Simple Bloomberg API test using the blpapi library directly. Connects to
    the local Bloomberg Terminal, sends a ReferenceDataRequest for AAPL US
    Equity (fields: PX_LAST, NAME), and writes detailed progress and results
    to an output file for debugging.

INPUT FILES:
    (none -- data is fetched live from Bloomberg Terminal)

OUTPUT FILES:
    ./test_results.txt
        Detailed log of the Bloomberg API test: session creation, connection
        status, data request progress, and retrieved field values. Written
        to the current working directory.

VERSION: 1.0
LAST UPDATED: 2026-06-05
AUTHOR: Arjun Divecha

DEPENDENCIES:
    - blpapi

USAGE:
    python test_blpapi_simple.py

NOTES:
    - Bloomberg Terminal must be running and logged in on localhost:8194.
    - Output is written incrementally (flushed after each write) to allow
      real-time debugging.
=============================================================================
"""
import sys

try:
    import blpapi
    print("blpapi imported successfully")
except ImportError as e:
    print(f"ERROR: blpapi not installed: {e}")
    sys.exit(1)

# Write to file for debugging
with open("test_results.txt", "w", encoding="utf-8") as f:
    f.write("Starting Bloomberg API test...\n")
    f.flush()
    
    try:
        # Create session
        f.write("Creating session...\n")
        f.flush()
        session_options = blpapi.SessionOptions()
        session_options.setServerHost("localhost")
        session_options.setServerPort(8194)
        
        session = blpapi.Session(session_options)
        f.write("Session created, starting...\n")
        f.flush()
        
        if session.start():
            f.write("[OK] Session started\n")
            f.flush()
            
            # Try to open service
            if session.openService("//blp/refdata"):
                f.write("[OK] Reference data service opened\n")
                f.flush()
                
                # Get service and create request
                service = session.getService("//blp/refdata")
                request = service.createRequest("ReferenceDataRequest")
                request.getElement("securities").appendValue("AAPL US Equity")
                request.getElement("fields").appendValue("PX_LAST")
                request.getElement("fields").appendValue("NAME")
                
                f.write("Sending request for AAPL...\n")
                f.flush()
                session.sendRequest(request)
                
                # Process response
                f.write("Waiting for response...\n")
                f.flush()
                while True:
                    event = session.nextEvent(10000)
                    if event.eventType() == blpapi.Event.RESPONSE or \
                       event.eventType() == blpapi.Event.PARTIAL_RESPONSE:
                        for msg in event:
                            if msg.hasElement("securityData"):
                                security_data = msg.getElement("securityData")
                                for i in range(security_data.numValues()):
                                    security = security_data.getValue(i)
                                    if security.hasElement("fieldData"):
                                        field_data = security.getElement("fieldData")
                                        if field_data.hasElement("PX_LAST"):
                                            price = field_data.getElementAsString("PX_LAST")
                                            f.write(f"Price: {price}\n")
                                        if field_data.hasElement("NAME"):
                                            name = field_data.getElementAsString("NAME")
                                            f.write(f"Name: {name}\n")
                    
                    if event.eventType() == blpapi.Event.RESPONSE:
                        break
                
                f.write("[OK] Data retrieved successfully\n")
            else:
                f.write("[ERROR] Failed to open reference data service\n")
            
            session.stop()
            f.write("[OK] Session stopped\n")
        else:
            f.write("[ERROR] Failed to start session\n")
            f.write("Make sure Bloomberg Terminal is running and logged in\n")
            
    except Exception as e:
        f.write(f"[ERROR] Exception: {e}\n")
        import traceback
        f.write(traceback.format_exc())

print("Test completed - check test_results.txt for output")

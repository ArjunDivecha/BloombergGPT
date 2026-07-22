"""
INPUT FILES:
- None (connects directly to Bloomberg Terminal)

OUTPUT FILES:
- None (prints results to console)

Bloomberg API (blpapi) Test Program
====================================
This is a minimal test program that demonstrates how to:
1. Connect to Bloomberg Terminal via blpapi
2. Create a session
3. Request reference data for a security
4. Process and display the response
5. Clean up the session

Requirements:
- Bloomberg Terminal must be running and logged in
- blpapi library must be installed (from Bloomberg's API portal)
- Default connection: localhost:8194

Author: BloombergGPT Test Program
Date: 2026-02-05
"""

import sys

# Try to import blpapi - exit gracefully if not available
try:
    import blpapi
except ImportError:
    print("ERROR: blpapi module not installed.")
    print("Install blpapi from Bloomberg's API portal before running this script.")
    sys.exit(1)


def create_bloomberg_session(host="localhost", port=8194):
    """
    Create and start a Bloomberg API session.
    
    Args:
        host: Bloomberg server hostname (default: localhost)
        port: Bloomberg server port (default: 8194)
    
    Returns:
        blpapi.Session object if successful, None otherwise
    """
    print(f"Creating Bloomberg session: {host}:{port}")
    
    # Create session options
    session_options = blpapi.SessionOptions()
    session_options.setServerHost(host)
    session_options.setServerPort(port)
    session_options.setConnectTimeout(5000)  # 5 second timeout
    
    # Create and start session
    session = blpapi.Session(session_options)
    
    if not session.start():
        print("ERROR: Failed to start Bloomberg session")
        print("Make sure Bloomberg Terminal is running and logged in")
        return None
    
    print("[OK] Bloomberg session started successfully")
    return session


def open_reference_data_service(session):
    """
    Open the Bloomberg reference data service.
    
    Args:
        session: Active Bloomberg session
    
    Returns:
        True if service opened successfully, False otherwise
    """
    print("Opening reference data service...")
    
    if not session.openService("//blp/refdata"):
        print("ERROR: Failed to open reference data service")
        return False
    
    print("[OK] Reference data service opened")
    return True


def get_reference_data(session, ticker, fields):
    """
    Request reference data from Bloomberg for a given security and fields.
    
    Args:
        session: Active Bloomberg session
        ticker: Security ticker (e.g., "AAPL US Equity")
        fields: List of field names (e.g., ["PX_LAST", "NAME"])
    
    Returns:
        Dictionary with field names as keys and values, or None if error
    """
    if not session:
        print("ERROR: No active session")
        return None
    
    try:
        # Get the reference data service
        ref_data_service = session.getService("//blp/refdata")
        
        # Create a reference data request
        request = ref_data_service.createRequest("ReferenceDataRequest")
        
        # Add the security (ensure proper format)
        if not any(suffix in ticker.upper() for suffix in 
                   [" EQUITY", " CORP", " GOVT", " INDEX", " CURNCY", " COMDTY"]):
            bloomberg_ticker = f"{ticker} US Equity"
        else:
            bloomberg_ticker = ticker
        
        print(f"Requesting data for: {bloomberg_ticker}")
        request.getElement("securities").appendValue(bloomberg_ticker)
        
        # Add fields to request
        print(f"Requesting fields: {fields}")
        for field in fields:
            request.getElement("fields").appendValue(field)
        
        # Send the request
        print("Sending request to Bloomberg...")
        session.sendRequest(request)
        
        # Process the response
        print("Waiting for response...")
        result = {}
        
        while True:
            # Wait for events (10 second timeout)
            event = session.nextEvent(10000)
            
            # Process response events
            if event.eventType() == blpapi.Event.RESPONSE or \
               event.eventType() == blpapi.Event.PARTIAL_RESPONSE:
                
                # Iterate through messages in the event
                for msg in event:
                    if msg.hasElement("securityData"):
                        security_data = msg.getElement("securityData")
                        
                        # Process each security in the response
                        for i in range(security_data.numValues()):
                            security = security_data.getValue(i)
                            security_name = security.getElementAsString("security")
                            
                            # Check for errors
                            if security.hasElement("securityError"):
                                error = security.getElement("securityError")
                                error_msg = error.getElementAsString("message")
                                print(f"ERROR for {security_name}: {error_msg}")
                                return None
                            
                            # Extract field data
                            if security.hasElement("fieldData"):
                                field_data = security.getElement("fieldData")
                                
                                for field in fields:
                                    if field_data.hasElement(field):
                                        value = field_data.getElementAsString(field)
                                        result[field] = value
                                        print(f"  {field}: {value}")
                                    else:
                                        result[field] = None
                                        print(f"  {field}: (not available)")
            
            # Break when we receive the final response
            if event.eventType() == blpapi.Event.RESPONSE:
                break
        
        return result
        
    except Exception as e:
        print(f"ERROR during data request: {e}")
        return None


def main():
    """
    Main test function - demonstrates basic Bloomberg API usage.
    """
    print("=" * 60)
    print("Bloomberg API (blpapi) Test Program")
    print("=" * 60)
    print()
    
    session = None
    
    try:
        # Step 1: Create session
        session = create_bloomberg_session()
        if not session:
            return
        
        # Step 2: Open reference data service
        if not open_reference_data_service(session):
            return
        
        # Step 3: Request data for a test security
        # Using Apple Inc. as an example
        ticker = "AAPL"
        fields = ["PX_LAST", "NAME", "CURRENCY", "EQY_SH_OUT"]
        
        print()
        print("-" * 60)
        result = get_reference_data(session, ticker, fields)
        print("-" * 60)
        
        # Step 4: Display results
        if result:
            print()
            print("[OK] Data retrieved successfully!")
            print()
            print("Results:")
            for field, value in result.items():
                print(f"  {field}: {value}")
        else:
            print()
            print("[ERROR] Failed to retrieve data")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nERROR: {e}")
    finally:
        # Step 5: Clean up - stop the session
        if session:
            print()
            print("Stopping Bloomberg session...")
            session.stop()
            print("[OK] Session stopped")
        
        print()
        print("=" * 60)
        print("Test completed")
        print("=" * 60)


if __name__ == "__main__":
    main()

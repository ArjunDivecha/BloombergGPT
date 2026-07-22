"""
============================================================================
BLPAPI TUTORIAL AND REFERENCE GUIDE
============================================================================

INPUT FILES:
- None (connects directly to Bloomberg Terminal via localhost:8194)

OUTPUT FILES:
- None (console output only, demonstrates proper usage patterns)

PURPOSE:
This program teaches developers how to correctly use the Bloomberg API (blpapi)
by demonstrating best practices, common patterns, and proper error handling.

REQUIREMENTS:
- Bloomberg Terminal running and logged in
- blpapi library installed (from Bloomberg's API portal)
- Connection to localhost:8194

AUTHOR: BloombergGPT Teaching Module
DATE: 2026-02-05
VERSION: 1.0

============================================================================
TABLE OF CONTENTS
============================================================================
1. Session Management (Creating, starting, stopping sessions)
2. Reference Data Requests (Single ticker, current values)
3. Batch Reference Data (Multiple tickers in one request)
4. Historical Data Requests (Time series data)
5. Error Handling Patterns (Proper exception handling)
6. Best Practices (Connection pooling, timeouts, cleanup)

============================================================================
"""

import sys
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta


# ============================================================================
# LESSON 1: IMPORTING AND CHECKING BLPAPI
# ============================================================================

def lesson_import_blpapi():
    """
    LESSON 1: How to properly import and verify blpapi installation
    
    KEY POINTS:
    - Always check if blpapi is installed before using it
    - Provide helpful error messages if not found
    - Use try/except for graceful failure
    """
    print("\n" + "=" * 80)
    print("LESSON 1: Importing and Verifying blpapi")
    print("=" * 80)
    
    try:
        import blpapi
        print("[OK] blpapi successfully imported")
        print(f"[INFO] blpapi version: {blpapi.__version__ if hasattr(blpapi, '__version__') else 'Unknown'}")
        return blpapi, True
    except ImportError as e:
        print(f"[ERROR] blpapi not installed: {e}")
        print("\nTo install blpapi:")
        print("1. Visit Bloomberg Professional Services portal")
        print("2. Download the appropriate wheel file for your platform")
        print("3. Install with: pip install path/to/blpapi-xxx.whl")
        return None, False


# ============================================================================
# LESSON 2: SESSION CREATION AND MANAGEMENT
# ============================================================================

def lesson_create_session(blpapi) -> Optional[Any]:
    """
    LESSON 2: How to properly create and configure a Bloomberg session
    
    KEY POINTS:
    - Use SessionOptions to configure connection parameters
    - Set appropriate timeouts (connect, keep-alive)
    - Always check if session.start() succeeds
    - Store session for reuse (don't create multiple sessions)
    """
    print("\n" + "=" * 80)
    print("LESSON 2: Creating and Starting a Session")
    print("=" * 80)
    
    print("\nStep 1: Create SessionOptions")
    print("-" * 80)
    print("CODE:")
    print("    session_options = blpapi.SessionOptions()")
    print("    session_options.setServerHost('localhost')")
    print("    session_options.setServerPort(8194)")
    print("    session_options.setConnectTimeout(5000)  # 5 seconds")
    print("    session_options.setDefaultKeepAliveInactivityTime(300)  # 5 minutes")
    
    session_options = blpapi.SessionOptions()
    session_options.setServerHost("localhost")
    session_options.setServerPort(8194)
    session_options.setConnectTimeout(5000)  # 5 seconds
    session_options.setDefaultKeepAliveInactivityTime(300)  # 5 minutes
    print("[OK] SessionOptions configured")
    
    print("\nStep 2: Create Session object")
    print("-" * 80)
    print("CODE:")
    print("    session = blpapi.Session(session_options)")
    
    session = blpapi.Session(session_options)
    print("[OK] Session object created")
    
    print("\nStep 3: Start the session")
    print("-" * 80)
    print("CODE:")
    print("    if not session.start():")
    print("        print('ERROR: Failed to start session')")
    print("        return None")
    
    if not session.start():
        print("[ERROR] Failed to start session")
        print("\nPossible causes:")
        print("- Bloomberg Terminal is not running")
        print("- Bloomberg Terminal is not logged in")
        print("- bbcomm.exe process is not active")
        print("- Port 8194 is blocked or in use")
        return None
    
    print("[OK] Session started successfully")
    print("\n[BEST PRACTICE] Reuse this session for multiple requests")
    print("[BEST PRACTICE] Don't create a new session for each request")
    
    return session


# ============================================================================
# LESSON 3: OPENING SERVICES
# ============================================================================

def lesson_open_service(blpapi, session) -> bool:
    """
    LESSON 3: How to open Bloomberg services
    
    KEY POINTS:
    - Different services for different data types
    - //blp/refdata - Reference and historical data
    - //blp/apiflds - Field information service
    - Always check if openService() succeeds
    """
    print("\n" + "=" * 80)
    print("LESSON 3: Opening Bloomberg Services")
    print("=" * 80)
    
    print("\nAvailable Services:")
    print("  - //blp/refdata    : Reference and historical data")
    print("  - //blp/apiflds    : Field information and search")
    print("  - //blp/mktdata    : Real-time market data")
    print("  - //blp/instruments: Instrument lookup")
    
    print("\nOpening Reference Data Service:")
    print("-" * 80)
    print("CODE:")
    print("    if not session.openService('//blp/refdata'):")
    print("        print('ERROR: Failed to open service')")
    print("        return False")
    
    if not session.openService("//blp/refdata"):
        print("[ERROR] Failed to open reference data service")
        return False
    
    print("[OK] Reference data service opened")
    print("\n[BEST PRACTICE] Open service once, use for multiple requests")
    
    return True


# ============================================================================
# LESSON 4: REFERENCE DATA REQUEST (SINGLE TICKER)
# ============================================================================

def lesson_reference_data_single(blpapi, session, ticker: str, fields: List[str]) -> Optional[Dict]:
    """
    LESSON 4: How to request reference data for a single ticker
    
    KEY POINTS:
    - Get service object using getService()
    - Create request using createRequest()
    - Add securities and fields to request
    - Send request and process events
    - Handle RESPONSE and PARTIAL_RESPONSE events
    """
    print("\n" + "=" * 80)
    print("LESSON 4: Reference Data Request (Single Ticker)")
    print("=" * 80)
    
    print(f"\nRequesting data for: {ticker}")
    print(f"Fields: {fields}")
    print("-" * 80)
    
    print("\nStep 1: Get the service and create request")
    print("CODE:")
    print("    service = session.getService('//blp/refdata')")
    print("    request = service.createRequest('ReferenceDataRequest')")
    
    try:
        service = session.getService("//blp/refdata")
        request = service.createRequest("ReferenceDataRequest")
        print("[OK] Request created")
        
        print("\nStep 2: Add security to request")
        print("CODE:")
        print(f"    request.getElement('securities').appendValue('{ticker}')")
        
        # Ensure proper Bloomberg format
        if not any(suffix in ticker.upper() for suffix in 
                   [" EQUITY", " CORP", " GOVT", " INDEX", " CURNCY", " COMDTY"]):
            bloomberg_ticker = f"{ticker} US Equity"
        else:
            bloomberg_ticker = ticker
        
        request.getElement("securities").appendValue(bloomberg_ticker)
        print(f"[OK] Added security: {bloomberg_ticker}")
        
        print("\nStep 3: Add fields to request")
        print("CODE:")
        for field in fields:
            print(f"    request.getElement('fields').appendValue('{field}')")
            request.getElement("fields").appendValue(field)
        print(f"[OK] Added {len(fields)} fields")
        
        print("\nStep 4: Send request")
        print("CODE:")
        print("    session.sendRequest(request)")
        
        session.sendRequest(request)
        print("[OK] Request sent to Bloomberg")
        
        print("\nStep 5: Process response events")
        print("CODE:")
        print("    while True:")
        print("        event = session.nextEvent(10000)  # 10 second timeout")
        print("        if event.eventType() == blpapi.Event.RESPONSE:")
        print("            # Process messages...")
        print("            break")
        
        result = {}
        
        while True:
            event = session.nextEvent(10000)  # 10 second timeout
            
            if event.eventType() == blpapi.Event.RESPONSE or \
               event.eventType() == blpapi.Event.PARTIAL_RESPONSE:
                
                for msg in event:
                    if msg.hasElement("securityData"):
                        security_data = msg.getElement("securityData")
                        
                        for i in range(security_data.numValues()):
                            security = security_data.getValue(i)
                            
                            # Check for errors
                            if security.hasElement("securityError"):
                                error = security.getElement("securityError")
                                error_msg = error.getElementAsString("message")
                                print(f"[ERROR] Security error: {error_msg}")
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
            
            if event.eventType() == blpapi.Event.RESPONSE:
                break
        
        print("\n[OK] Data retrieved successfully")
        return result
        
    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================================
# LESSON 5: BATCH REFERENCE DATA REQUEST
# ============================================================================

def lesson_reference_data_batch(blpapi, session, tickers: List[str], fields: List[str]) -> Optional[Dict]:
    """
    LESSON 5: How to request data for multiple tickers in one request
    
    KEY POINTS:
    - More efficient than multiple single requests
    - Add multiple securities to request
    - Response contains data for all securities
    - Process each security in the response
    """
    print("\n" + "=" * 80)
    print("LESSON 5: Batch Reference Data Request (Multiple Tickers)")
    print("=" * 80)
    
    print(f"\nRequesting data for {len(tickers)} tickers: {tickers}")
    print(f"Fields: {fields}")
    print("-" * 80)
    
    print("\n[BEST PRACTICE] Use batch requests for multiple tickers")
    print("[BEST PRACTICE] Much faster than individual requests")
    
    try:
        service = session.getService("//blp/refdata")
        request = service.createRequest("ReferenceDataRequest")
        
        print("\nAdding multiple securities:")
        print("CODE:")
        print("    for ticker in tickers:")
        print("        request.getElement('securities').appendValue(ticker)")
        
        bloomberg_tickers = []
        for ticker in tickers:
            if not any(suffix in ticker.upper() for suffix in 
                       [" EQUITY", " CORP", " GOVT", " INDEX", " CURNCY", " COMDTY"]):
                bloomberg_ticker = f"{ticker} US Equity"
            else:
                bloomberg_ticker = ticker
            bloomberg_tickers.append(bloomberg_ticker)
            request.getElement("securities").appendValue(bloomberg_ticker)
            print(f"  Added: {bloomberg_ticker}")
        
        for field in fields:
            request.getElement("fields").appendValue(field)
        
        session.sendRequest(request)
        print(f"\n[OK] Batch request sent for {len(tickers)} tickers")
        
        results = {}
        
        while True:
            event = session.nextEvent(10000)
            
            if event.eventType() == blpapi.Event.RESPONSE or \
               event.eventType() == blpapi.Event.PARTIAL_RESPONSE:
                
                for msg in event:
                    if msg.hasElement("securityData"):
                        security_data = msg.getElement("securityData")
                        
                        for i in range(security_data.numValues()):
                            security = security_data.getValue(i)
                            security_name = security.getElementAsString("security")
                            
                            if security.hasElement("securityError"):
                                error = security.getElement("securityError")
                                error_msg = error.getElementAsString("message")
                                results[security_name] = {"error": error_msg}
                                continue
                            
                            if security.hasElement("fieldData"):
                                field_data = security.getElement("fieldData")
                                ticker_data = {}
                                
                                for field in fields:
                                    if field_data.hasElement(field):
                                        value = field_data.getElementAsString(field)
                                        ticker_data[field] = value
                                    else:
                                        ticker_data[field] = None
                                
                                results[security_name] = ticker_data
            
            if event.eventType() == blpapi.Event.RESPONSE:
                break
        
        print(f"\n[OK] Retrieved data for {len(results)} securities")
        
        for ticker, data in results.items():
            print(f"\n{ticker}:")
            for field, value in data.items():
                print(f"  {field}: {value}")
        
        return results
        
    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")
        return None


# ============================================================================
# LESSON 6: HISTORICAL DATA REQUEST
# ============================================================================

def lesson_historical_data(blpapi, session, ticker: str, fields: List[str], 
                          start_date: str, end_date: str) -> Optional[List[Dict]]:
    """
    LESSON 6: How to request historical time series data
    
    KEY POINTS:
    - Use HistoricalDataRequest instead of ReferenceDataRequest
    - Specify start and end dates (YYYYMMDD format)
    - Can set periodicity (DAILY, WEEKLY, MONTHLY)
    - Response contains time series with dates
    """
    print("\n" + "=" * 80)
    print("LESSON 6: Historical Data Request")
    print("=" * 80)
    
    print(f"\nRequesting historical data for: {ticker}")
    print(f"Fields: {fields}")
    print(f"Period: {start_date} to {end_date}")
    print("-" * 80)
    
    print("\n[NOTE] Historical data uses HistoricalDataRequest")
    print("[NOTE] Dates must be in YYYYMMDD format")
    
    try:
        service = session.getService("//blp/refdata")
        request = service.createRequest("HistoricalDataRequest")
        
        print("\nCODE:")
        print("    request = service.createRequest('HistoricalDataRequest')")
        print(f"    request.getElement('securities').appendValue('{ticker}')")
        print(f"    request.set('startDate', '{start_date}')")
        print(f"    request.set('endDate', '{end_date}')")
        print("    request.set('periodicitySelection', 'DAILY')")
        
        if not any(suffix in ticker.upper() for suffix in 
                   [" EQUITY", " CORP", " GOVT", " INDEX", " CURNCY", " COMDTY"]):
            bloomberg_ticker = f"{ticker} US Equity"
        else:
            bloomberg_ticker = ticker
        
        request.getElement("securities").appendValue(bloomberg_ticker)
        
        for field in fields:
            request.getElement("fields").appendValue(field)
        
        request.set("startDate", start_date)
        request.set("endDate", end_date)
        request.set("periodicitySelection", "DAILY")
        
        session.sendRequest(request)
        print("\n[OK] Historical data request sent")
        
        results = []
        
        while True:
            event = session.nextEvent(10000)
            
            if event.eventType() == blpapi.Event.RESPONSE or \
               event.eventType() == blpapi.Event.PARTIAL_RESPONSE:
                
                for msg in event:
                    if msg.hasElement("securityData"):
                        security_data = msg.getElement("securityData")
                        security = security_data.getElement("securityData")
                        
                        if security.hasElement("fieldData"):
                            field_data_array = security.getElement("fieldData")
                            
                            for i in range(field_data_array.numValues()):
                                field_data = field_data_array.getValue(i)
                                
                                data_point = {}
                                
                                if field_data.hasElement("date"):
                                    date_value = field_data.getElementAsString("date")
                                    data_point["date"] = date_value
                                
                                for field in fields:
                                    if field_data.hasElement(field):
                                        value = field_data.getElementAsString(field)
                                        data_point[field] = value
                                
                                results.append(data_point)
            
            if event.eventType() == blpapi.Event.RESPONSE:
                break
        
        print(f"\n[OK] Retrieved {len(results)} data points")
        
        # Show first and last few points
        if results:
            print("\nFirst 3 data points:")
            for i, point in enumerate(results[:3]):
                print(f"  {point}")
            
            if len(results) > 6:
                print("  ...")
            
            print("\nLast 3 data points:")
            for i, point in enumerate(results[-3:]):
                print(f"  {point}")
        
        return results
        
    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")
        return None


# ============================================================================
# LESSON 7: PROPER SESSION CLEANUP
# ============================================================================

def lesson_cleanup(session):
    """
    LESSON 7: How to properly clean up sessions
    
    KEY POINTS:
    - Always stop session when done
    - Use try/finally to ensure cleanup
    - Don't leave sessions hanging
    """
    print("\n" + "=" * 80)
    print("LESSON 7: Proper Session Cleanup")
    print("=" * 80)
    
    print("\n[BEST PRACTICE] Always stop session when done")
    print("[BEST PRACTICE] Use try/finally to ensure cleanup")
    print("\nCODE:")
    print("    try:")
    print("        # Do your work")
    print("        pass")
    print("    finally:")
    print("        if session:")
    print("            session.stop()")
    
    if session:
        session.stop()
        print("\n[OK] Session stopped cleanly")


# ============================================================================
# LESSON 8: ERROR HANDLING PATTERNS
# ============================================================================

def lesson_error_handling():
    """
    LESSON 8: Proper error handling patterns for blpapi
    """
    print("\n" + "=" * 80)
    print("LESSON 8: Error Handling Best Practices")
    print("=" * 80)
    
    print("\n1. Always check if session starts:")
    print("-" * 80)
    print("    if not session.start():")
    print("        print('ERROR: Bloomberg Terminal not connected')")
    print("        return None")
    
    print("\n2. Always check if service opens:")
    print("-" * 80)
    print("    if not session.openService('//blp/refdata'):")
    print("        print('ERROR: Failed to open service')")
    print("        return None")
    
    print("\n3. Check for security errors in response:")
    print("-" * 80)
    print("    if security.hasElement('securityError'):")
    print("        error = security.getElement('securityError')")
    print("        error_msg = error.getElementAsString('message')")
    print("        print(f'ERROR: {error_msg}')")
    
    print("\n4. Use try/except for unexpected errors:")
    print("-" * 80)
    print("    try:")
    print("        # Your blpapi code")
    print("    except Exception as e:")
    print("        print(f'ERROR: {e}')")
    print("        # Handle error appropriately")
    
    print("\n5. Use try/finally for cleanup:")
    print("-" * 80)
    print("    try:")
    print("        session = create_session()")
    print("        # Do work")
    print("    finally:")
    print("        if session:")
    print("            session.stop()")


# ============================================================================
# LESSON 9: BEST PRACTICES SUMMARY
# ============================================================================

def lesson_best_practices():
    """
    LESSON 9: Best practices summary
    """
    print("\n" + "=" * 80)
    print("LESSON 9: Best Practices Summary")
    print("=" * 80)
    
    print("\n1. SESSION MANAGEMENT")
    print("-" * 80)
    print("  - Create session once, reuse for multiple requests")
    print("  - Don't create new session for each request")
    print("  - Set appropriate timeouts (5-10 seconds)")
    print("  - Always stop session when done")
    
    print("\n2. REQUEST OPTIMIZATION")
    print("-" * 80)
    print("  - Use batch requests for multiple tickers")
    print("  - Request only fields you need")
    print("  - Reuse service objects")
    print("  - Set reasonable timeout in nextEvent()")
    
    print("\n3. ERROR HANDLING")
    print("-" * 80)
    print("  - Check all return values (start, openService)")
    print("  - Check for securityError in responses")
    print("  - Use try/except for unexpected errors")
    print("  - Use try/finally for cleanup")
    
    print("\n4. DATA FORMATTING")
    print("-" * 80)
    print("  - Ensure tickers have proper format (e.g., 'AAPL US Equity')")
    print("  - Use correct date format for historical data (YYYYMMDD)")
    print("  - Check if fields exist before accessing")
    
    print("\n5. PERFORMANCE")
    print("-" * 80)
    print("  - Connection pooling: reuse sessions")
    print("  - Batch requests: multiple tickers in one call")
    print("  - Appropriate timeouts: don't wait too long")
    print("  - Clean up: stop sessions to free resources")


# ============================================================================
# MAIN TUTORIAL RUNNER
# ============================================================================

def run_tutorial(interactive: bool = True):
    """
    Run the complete blpapi tutorial
    
    Args:
        interactive: If True, wait for user input between lessons
    """
    print("\n" + "=" * 80)
    print("BLOOMBERG API (blpapi) COMPREHENSIVE TUTORIAL")
    print("=" * 80)
    print("\nThis tutorial demonstrates proper blpapi usage patterns")
    print("Follow along with the code examples and explanations")
    print("=" * 80)
    
    # Lesson 1: Import
    blpapi, success = lesson_import_blpapi()
    if not success:
        return
    
    if interactive:
        input("\nPress Enter to continue to Lesson 2...")
    
    # Lesson 2: Create session
    session = lesson_create_session(blpapi)
    if not session:
        return
    
    try:
        if interactive:
            input("\nPress Enter to continue to Lesson 3...")
        
        # Lesson 3: Open service
        if not lesson_open_service(blpapi, session):
            return
        
        if interactive:
            input("\nPress Enter to continue to Lesson 4...")
        
        # Lesson 4: Single ticker reference data
        lesson_reference_data_single(blpapi, session, "AAPL", ["PX_LAST", "NAME", "CURRENCY"])
        
        if interactive:
            input("\nPress Enter to continue to Lesson 5...")
        
        # Lesson 5: Batch reference data
        lesson_reference_data_batch(blpapi, session, ["AAPL", "MSFT", "GOOGL"], ["PX_LAST", "NAME"])
        
        if interactive:
            input("\nPress Enter to continue to Lesson 6...")
        
        # Lesson 6: Historical data
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
        lesson_historical_data(blpapi, session, "AAPL", ["PX_LAST"], start_date, end_date)
        
        if interactive:
            input("\nPress Enter to continue to Lesson 7...")
        
        # Lesson 7: Cleanup
        lesson_cleanup(session)
        session = None  # Prevent double cleanup
        
        if interactive:
            input("\nPress Enter to continue to Lesson 8...")
        
        # Lesson 8: Error handling
        lesson_error_handling()
        
        if interactive:
            input("\nPress Enter to continue to Lesson 9...")
        
        # Lesson 9: Best practices
        lesson_best_practices()
        
    finally:
        # Ensure cleanup
        if session:
            session.stop()
    
    print("\n" + "=" * 80)
    print("TUTORIAL COMPLETE!")
    print("=" * 80)
    print("\nYou now know how to:")
    print("  1. Create and manage Bloomberg sessions")
    print("  2. Request reference data (single and batch)")
    print("  3. Request historical time series data")
    print("  4. Handle errors properly")
    print("  5. Follow best practices for performance")
    print("\nUse this program as a reference for your own implementations!")
    print("=" * 80)


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Bloomberg API (blpapi) Tutorial")
    parser.add_argument("--non-interactive", action="store_true", 
                       help="Run without waiting for user input between lessons")
    parser.add_argument("--lesson", type=int, choices=range(1, 10),
                       help="Run a specific lesson only (1-9)")
    
    args = parser.parse_args()
    
    if args.lesson:
        # Run specific lesson
        blpapi, success = lesson_import_blpapi()
        if not success:
            sys.exit(1)
        
        if args.lesson == 1:
            pass  # Already ran
        elif args.lesson == 2:
            lesson_create_session(blpapi)
        elif args.lesson >= 3:
            session = lesson_create_session(blpapi)
            if session:
                try:
                    if args.lesson == 3:
                        lesson_open_service(blpapi, session)
                    elif args.lesson == 4:
                        if lesson_open_service(blpapi, session):
                            lesson_reference_data_single(blpapi, session, "AAPL", ["PX_LAST", "NAME"])
                    elif args.lesson == 5:
                        if lesson_open_service(blpapi, session):
                            lesson_reference_data_batch(blpapi, session, ["AAPL", "MSFT"], ["PX_LAST"])
                    elif args.lesson == 6:
                        if lesson_open_service(blpapi, session):
                            end = datetime.now().strftime("%Y%m%d")
                            start = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
                            lesson_historical_data(blpapi, session, "AAPL", ["PX_LAST"], start, end)
                    elif args.lesson == 7:
                        lesson_cleanup(session)
                        session = None
                    elif args.lesson == 8:
                        lesson_error_handling()
                    elif args.lesson == 9:
                        lesson_best_practices()
                finally:
                    if session:
                        session.stop()
    else:
        # Run full tutorial
        run_tutorial(interactive=not args.non_interactive)

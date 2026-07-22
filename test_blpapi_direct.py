"""
=============================================================================
SCRIPT NAME: test_blpapi_direct.py
=============================================================================

DESCRIPTION:
    Direct blpapi connection test that verifies Bloomberg Terminal
    accessibility without any broker or FastAPI dependencies. Tests blpapi
    installation, session creation, session start (connecting to
    localhost:8194), and reference data service availability.

INPUT FILES:
    (none -- tests live Bloomberg connection only)

OUTPUT FILES:
    (none -- results are printed to stdout)

VERSION: 1.0
LAST UPDATED: 2026-06-05
AUTHOR: Arjun Divecha

DEPENDENCIES:
    - blpapi

USAGE:
    python test_blpapi_direct.py

NOTES:
    - Bloomberg Terminal must be running and logged in locally.
    - The bbcomm.exe process must be active.
    - Exits with status 1 if any step fails.
=============================================================================
"""
import sys

print("=" * 60)
print("BLPAPI Direct Connection Test")
print("=" * 60)
print()

# Step 1: Check if blpapi is installed
print("[1/4] Checking if blpapi is installed...")
try:
    import blpapi
    print("  [OK] blpapi module found")
except ImportError as e:
    print(f"  [ERROR] blpapi not installed: {e}")
    print()
    print("  To install blpapi:")
    print("  1. Download from Bloomberg Professional Services portal")
    print("  2. Install with: pip install path/to/blpapi-xxx.whl")
    sys.exit(1)

# Step 2: Try to create session
print()
print("[2/4] Creating Bloomberg session...")
try:
    session_options = blpapi.SessionOptions()
    session_options.setServerHost("localhost")
    session_options.setServerPort(8194)
    session_options.setConnectTimeout(5000)
    
    session = blpapi.Session(session_options)
    print("  [OK] Session object created")
except Exception as e:
    print(f"  [ERROR] Failed to create session: {e}")
    sys.exit(1)

# Step 3: Try to start session
print()
print("[3/4] Starting Bloomberg session (connecting to localhost:8194)...")
try:
    if session.start():
        print("  [OK] Session started successfully!")
        print("  [OK] Connected to Bloomberg Terminal")
        
        # Step 4: Try to open service
        print()
        print("[4/4] Opening reference data service...")
        if session.openService("//blp/refdata"):
            print("  [OK] Reference data service opened")
            print()
            print("=" * 60)
            print("SUCCESS: Bloomberg Terminal is accessible via blpapi!")
            print("=" * 60)
            print()
            print("Next steps:")
            print("- You can now use blpapi to request data")
            print("- Try running: python test_blpapi.py")
        else:
            print("  [ERROR] Failed to open reference data service")
        
        session.stop()
        print("  [OK] Session stopped cleanly")
    else:
        print("  [ERROR] Failed to start session")
        print()
        print("Possible reasons:")
        print("1. Bloomberg Terminal is not running")
        print("2. Bloomberg Terminal is not logged in")
        print("3. bbcomm.exe process is not active")
        print()
        print("Solutions:")
        print("1. Launch Bloomberg Terminal")
        print("2. Log in with your credentials")
        print("3. Wait for the terminal to fully load")
        print("4. Check Task Manager for bbcomm.exe process")
        sys.exit(1)
except Exception as e:
    print(f"  [ERROR] Exception: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("Test completed")
print("=" * 60)

#!/usr/bin/env python3
"""
Single Command Bloomberg Natural Language Interface Launcher
Runs everything: main server + ngrok tunnel
"""

import subprocess
import sys
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def start_main_server():
    """Start the Bloomberg broker server"""
    print("🚀 Starting Bloomberg Data Broker...")
    try:
        # Start main.py in background (don't pipe stdout/stderr so we can see output)
        server = subprocess.Popen(
            [sys.executable, "main.py"],
            # stdout=subprocess.PIPE,
            # stderr=subprocess.PIPE,
            # text=True
        )
        print("✅ Main server started (PID: {})".format(server.pid))
        return server
    except Exception as e:
        print(f"❌ Failed to start main server: {e}")
        return None

def start_ngrok():
    """Start ngrok tunnel"""
    print("🚇 Starting ngrok tunnel...")
    try:
        # Start ngrok in background
        ngrok = subprocess.Popen(
            [sys.executable, "start_ngrok.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print("✅ ngrok started (PID: {})".format(ngrok.pid))
        return ngrok
    except Exception as e:
        print(f"❌ Failed to start ngrok: {e}")
        return None

def monitor_processes():
    """Monitor the running processes"""
    port = os.getenv("BROKER_PORT", "8000")
    print("\n📊 System Status:")
    print("-" * 30)

    try:
        # Check if processes are running
        result = subprocess.run(['tasklist'], capture_output=True, text=True, timeout=10)

        python_running = 'python.exe' in result.stdout
        ngrok_running = 'ngrok.exe' in result.stdout

        if python_running:
            print("✅ Main server: RUNNING")
        else:
            print("❌ Main server: NOT RUNNING")

        if ngrok_running:
            print("✅ ngrok tunnel: RUNNING")
        else:
            print("❌ ngrok tunnel: NOT RUNNING")

    except Exception as e:
        print(f"⚠️ Could not check process status: {e}")

    print("\n🌐 API Endpoints:")
    print(f"   - http://localhost:{port}/blp/fields")
    print(f"   - http://localhost:{port}/blp/nlquery?query=Apple+stock+price")
    print(f"   - http://localhost:{port}/blp/refdata?ticker=AAPL+US+Equity&fields=PX_LAST")

def main():
    print("=" * 60)
    print("🌟 Bloomberg Natural Language Interface")
    print("   Single Command Launcher")
    print("=" * 60)
    print()

    # Kill any existing processes
    print("🧹 Cleaning up old processes...")
    try:
        # Kill python processes (but not the current one)
        result = subprocess.run(['taskkill', '/f', '/im', 'python.exe'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Python processes killed")
        elif "not found" in result.stderr.lower():
            print("ℹ️ No Python processes to kill")
        else:
            print(f"⚠️ Warning killing Python processes: {result.stderr}")

        # Kill ngrok processes
        result = subprocess.run(['taskkill', '/f', '/im', 'ngrok.exe'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ ngrok processes killed")
        elif "not found" in result.stderr.lower():
            print("ℹ️ No ngrok processes to kill")
        else:
            print(f"⚠️ Warning killing ngrok processes: {result.stderr}")

        time.sleep(2)  # Wait for processes to die
    except Exception as e:
        print(f"⚠️ Warning during cleanup: {e}")
        pass

    # Start main server
    server_process = start_main_server()
    if not server_process:
        print("❌ Cannot continue without main server")
        return

    # Wait for server to start
    time.sleep(5)

    # Start ngrok
    ngrok_process = start_ngrok()
    if not ngrok_process:
        print("⚠️ ngrok failed to start, but main server is running")

    # Monitor status
    time.sleep(5)
    monitor_processes()

    print("\n🎉 System started successfully!")
    print("📝 Check the terminal windows for server and ngrok output")
    print("🔍 Use Ctrl+C to stop everything")
    print()

    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        if server_process:
            server_process.terminate()
        if ngrok_process:
            ngrok_process.terminate()
        print("✅ All processes stopped")

if __name__ == "__main__":
    main()

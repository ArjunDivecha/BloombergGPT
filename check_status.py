#!/usr/bin/env python3
"""
Bloomberg Data Broker System Status Monitor
Real-time monitoring of all system components
"""

import os
import sys
import time
import requests
import subprocess
# Configuration hardcoded (no environment variables needed)

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def check_bloomberg_api():
    """Check if Bloomberg API is available"""
    try:
        import blpapi
        return True, "✅ Bloomberg API available"
    except ImportError:
        return False, "❌ Bloomberg API not installed"

def check_bloomberg_connection():
    """Check Bloomberg Terminal connection"""
    try:
        import blpapi
        sessionOptions = blpapi.SessionOptions()
        sessionOptions.setServerHost("localhost")
        sessionOptions.setServerPort(8194)
        session = blpapi.Session(sessionOptions)
        
        if session.start():
            session.stop()
            return True, "✅ Bloomberg Terminal connected"
        else:
            return False, "❌ Bloomberg Terminal not responding"
    except Exception as e:
        return False, f"❌ Bloomberg connection error: {str(e)[:50]}"

def check_broker_running():
    """Check if Bloomberg Broker is running"""
    port = 8000
    try:
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True, timeout=5)
        if f":{port}" in result.stdout:
            return True, f"✅ Bloomberg Broker running on port {port}"
        else:
            return False, f"❌ Bloomberg Broker not running on port {port}"
    except:
        return False, "❌ Cannot check broker status"

def check_broker_api():
    """Check if Bloomberg Broker API is responding"""
    try:
        port = 8000
        api_key = "Caeser00**"
        
        response = requests.get(
            f'http://localhost:{port}/blp/fields',
            headers={'x-api-key': api_key},
            timeout=5
        )
        
        if response.status_code == 200:
            return True, "✅ Broker API responding correctly"
        else:
            return False, f"❌ Broker API error (HTTP {response.status_code})"
    except requests.exceptions.ConnectionError:
        return False, "❌ Broker API not responding (connection refused)"
    except Exception as e:
        return False, f"❌ Broker API error: {str(e)[:50]}"

def check_ngrok_running():
    """Check if ngrok is running"""
    try:
        result = subprocess.run(['tasklist'], capture_output=True, text=True, timeout=5)
        if 'ngrok.exe' in result.stdout:
            return True, "✅ ngrok tunnel running"
        else:
            return False, "❌ ngrok tunnel not running"
    except:
        return False, "❌ Cannot check ngrok status"

def check_env_config():
    """Check environment configuration"""
    issues = []
    
    api_key = "Caeser00**"
    if not api_key:
        issues.append("API_KEY not set")
    
    ngrok_token = "32zjqBzQsKJ8Gtp9lxVMO3aqs7O_6zVut1EthKzT4cebGXwt4"
    if not ngrok_token or ngrok_token == "your_ngrok_authtoken_here":
        issues.append("NGROK_AUTHTOKEN not configured")
    
    if issues:
        return False, f"❌ Config issues: {', '.join(issues)}"
    else:
        return True, "✅ Configuration valid"

def get_system_status():
    """Get overall system status"""
    checks = [
        ("Environment Config", check_env_config),
        ("Bloomberg API", check_bloomberg_api),
        ("Bloomberg Connection", check_bloomberg_connection),
        ("Broker Process", check_broker_running),
        ("Broker API", check_broker_api),
        ("ngrok Tunnel", check_ngrok_running),
    ]
    
    results = []
    all_ok = True
    
    for name, check_func in checks:
        try:
            status, message = check_func()
            results.append((name, status, message))
            if not status:
                all_ok = False
        except Exception as e:
            results.append((name, False, f"❌ Error: {str(e)[:50]}"))
            all_ok = False
    
    return results, all_ok

def main():
    """Main status monitoring loop"""
    # Configuration is hardcoded - no need to load dotenv
    
    print("Bloomberg Data Broker - System Status Monitor")
    print("=" * 60)
    print("Press Ctrl+C to exit")
    print()
    
    try:
        while True:
            clear_screen()
            
            print("🔍 Bloomberg Data Broker System Status")
            print("=" * 50)
            print(f"⏰ Last Update: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            
            # Get system status
            results, all_ok = get_system_status()
            
            # Display results
            for name, status, message in results:
                print(f"{name:20} {message}")
            
            print()
            print("=" * 50)
            
            if all_ok:
                print("🎉 System Status: ALL SYSTEMS OPERATIONAL")
                print("🚀 Your Bloomberg ChatGPT is ready to use!")
            else:
                print("⚠️  System Status: ISSUES DETECTED")
                print("💡 Check the errors above and restart components as needed")
            
            print()
            print("Commands:")
            print("- Start System: start_bloomberg_broker.bat")
            print("- Stop System: stop_bloomberg_broker.bat")
            print("- This updates every 10 seconds")
            print()
            
            # Wait 10 seconds before next check
            for i in range(10, 0, -1):
                print(f"\rNext update in {i} seconds... ", end="", flush=True)
                time.sleep(1)
            print()
            
    except KeyboardInterrupt:
        print("\n\n👋 System monitoring stopped")
        print("Bloomberg Data Broker may still be running")

if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
ngrok Tunnel Starter with Environment Configuration
Automatically configures and starts ngrok tunnel using .env settings
"""

import os
import sys
import subprocess
import time
from dotenv import load_dotenv

def find_ngrok_executable():
    """Find ngrok executable in common locations"""
    possible_paths = [
        "./ngrok.exe",
        "./ngrok",
        "ngrok.exe",
        "ngrok",
        "\\\\Mac\\Home\\Downloads\\ngrok-v3-stable-windows-arm64\\ngrok.exe",
        os.path.expanduser("~/Downloads/ngrok.exe"),
        os.path.expanduser("~/Downloads/ngrok"),
    ]
    
    for path in possible_paths:
        if os.path.isfile(path):
            return path
    
    return None

def setup_ngrok_auth(authtoken):
    """Setup ngrok authentication token"""
    ngrok_path = find_ngrok_executable()
    if not ngrok_path:
        print("❌ ERROR: ngrok executable not found!")
        return False
    
    try:
        # Configure authtoken
        result = subprocess.run([ngrok_path, "config", "add-authtoken", authtoken], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ ngrok authtoken configured successfully")
            return True
        else:
            print(f"❌ Failed to configure ngrok authtoken: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error configuring ngrok: {e}")
        return False

def start_ngrok_tunnel(port=8000, subdomain=None, region="us"):
    """Start ngrok tunnel"""
    ngrok_path = find_ngrok_executable()
    if not ngrok_path:
        print("❌ ERROR: ngrok executable not found!")
        return False
    
    # Build ngrok command
    cmd = [ngrok_path, "http", str(port)]
    
    if subdomain:
        cmd.extend(["--subdomain", subdomain])
    
    if region:
        cmd.extend(["--region", region])
    
    try:
        print(f"🚀 Starting ngrok tunnel: {' '.join(cmd)}")
        # Start ngrok in background
        process = subprocess.Popen(cmd)
        
        # Give ngrok time to start
        time.sleep(5)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ ngrok tunnel started successfully!")
            print("🌐 Check the ngrok window for your HTTPS URL")
            return True
        else:
            print("❌ ngrok tunnel failed to start")
            return False
            
    except Exception as e:
        print(f"❌ Error starting ngrok tunnel: {e}")
        return False

def main():
    print("=" * 50)
    print("🚇 ngrok Tunnel Starter")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    authtoken = os.getenv("NGROK_AUTHTOKEN")
    subdomain = os.getenv("NGROK_SUBDOMAIN")
    region = os.getenv("NGROK_REGION", "us")
    port = int(os.getenv("BROKER_PORT", "8000"))
    
    if not authtoken or authtoken == "your_ngrok_authtoken_here":
        print("❌ ERROR: NGROK_AUTHTOKEN not configured!")
        print("Please:")
        print("1. Get your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken")
        print("2. Add it to your .env file: NGROK_AUTHTOKEN=your_token_here")
        input("Press Enter to exit...")
        return False
    
    print(f"📋 Configuration:")
    print(f"   Port: {port}")
    print(f"   Region: {region}")
    if subdomain:
        print(f"   Subdomain: {subdomain}")
    print()
    
    # Setup authtoken
    print("🔑 Configuring ngrok authentication...")
    if not setup_ngrok_auth(authtoken):
        input("Press Enter to exit...")
        return False
    
    # Start tunnel
    print("🚇 Starting ngrok tunnel...")
    if start_ngrok_tunnel(port, subdomain, region):
        print()
        print("✅ ngrok tunnel is now running!")
        print("🔗 Your HTTPS URL will be displayed in the ngrok window")
        print("📋 Copy this URL to use in your ChatGPT Custom GPT")
        print()
        print("Press Ctrl+C to stop the tunnel")
        
        try:
            # Keep the script running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping ngrok tunnel...")
            return True
    else:
        input("Press Enter to exit...")
        return False

if __name__ == "__main__":
    main()

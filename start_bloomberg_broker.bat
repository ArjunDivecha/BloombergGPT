@echo off
title Bloomberg Data Broker Startup
echo ==========================================
echo Starting Bloomberg Data Broker System
echo ==========================================
echo.

echo [1/4] Checking configuration...
if not exist ".env" (
    echo ❌ ERROR: .env file not found!
    echo.
    echo Please create .env file from env.template:
    echo 1. Copy env.template to .env
    echo 2. Add your NGROK_AUTHTOKEN from https://dashboard.ngrok.com/get-started/your-authtoken
    echo 3. Update API_KEY if needed
    echo.
    pause
    exit /b 1
)
echo ✅ Configuration file found

echo.
echo [2/4] Starting Bloomberg Data Broker...
start "Bloomberg Broker" cmd /k "cd /d "%~dp0" && python main.py"
timeout /t 5 /nobreak > nul

echo.
echo [3/4] Starting ngrok tunnel with automatic configuration...
start "ngrok Tunnel" cmd /k "cd /d "%~dp0" && python start_ngrok.py"
timeout /t 10 /nobreak > nul

echo.
echo [4/4] Opening system status...
start "System Status" cmd /k "cd /d "%~dp0" && python check_status.py"

echo.
echo ==========================================
echo Bloomberg Data Broker System Started!
echo ==========================================
echo.
echo Check the opened windows:
echo - Bloomberg Broker: Running with your configured settings
echo - ngrok Tunnel: Automatically configured with your authtoken
echo - System Status: Real-time system health monitoring
echo.
echo Your Bloomberg ChatGPT is now ready to use!
echo.
pause

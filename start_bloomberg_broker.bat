@echo off
title Bloomberg Data Broker Startup

REM Handle UNC path by using pushd to map to drive letter
pushd "%~dp0"

echo ==========================================
echo Starting Bloomberg Data Broker System
echo ==========================================
echo.
echo Working directory: %CD%
echo.

echo [1/4] Checking configuration...
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo.
    echo Please create .env from env.template and set API_KEY, BLOOMBERG_HOST, etc.
    echo.
    pause
    popd
    exit /b 1
)
echo [OK] Configuration file found

echo.
echo [2/4] Starting Bloomberg Data Broker...
start "Bloomberg Broker" cmd /k "pushd "%~dp0" && python main.py"
timeout /t 5 /nobreak > nul

echo.
echo [3/4] Starting Cloudflare tunnel...
start "Cloudflare Tunnel" cmd /k "pushd "%~dp0" && start_cloudflared.bat"
timeout /t 8 /nobreak > nul

echo.
echo [4/4] Opening system status...
start "System Status" cmd /k "pushd "%~dp0" && python check_status.py"

echo.
echo ==========================================
echo Bloomberg Data Broker System Started!
echo ==========================================
echo.
echo Check the opened windows:
echo - Bloomberg Broker: Running with your configured settings
echo - Cloudflare Tunnel: Managed by start_cloudflared.bat
echo - System Status: Real-time system health monitoring
echo.
echo Your Bloomberg ChatGPT is now ready to use!
echo.
pause
popd

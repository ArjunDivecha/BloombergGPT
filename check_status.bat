@echo off
title Bloomberg Data Broker - System Status
echo ==========================================
echo Bloomberg Data Broker System Status
echo ==========================================
echo.

echo [Checking Bloomberg Terminal Connection...]
python -c "import blpapi; print('✓ Bloomberg API available')" 2>nul
if %errorlevel% == 0 (
    echo ✓ Bloomberg API: Available
) else (
    echo ✗ Bloomberg API: Not available - check Bloomberg Terminal
)

echo.
echo [Checking Bloomberg Broker...]
netstat -ano | findstr :8000 >nul
if %errorlevel% == 0 (
    echo ✓ Bloomberg Broker: Running on port 8000
) else (
    echo ✗ Bloomberg Broker: Not running
)

echo.
echo [Checking ngrok Tunnel...]
tasklist | findstr ngrok.exe >nul
if %errorlevel% == 0 (
    echo ✓ ngrok Tunnel: Running
    echo   Check ngrok window for HTTPS URL
) else (
    echo ✗ ngrok Tunnel: Not running
)

echo.
echo [Testing Broker Connection...]
python -c "
import requests
try:
    response = requests.get('http://localhost:8000/blp/fields', headers={'x-api-key': 'Caeser00**'}, timeout=5)
    if response.status_code == 200:
        print('✓ Broker API: Responding correctly')
    else:
        print('✗ Broker API: Error response (' + str(response.status_code) + ')')
except:
    print('✗ Broker API: Not responding')
" 2>nul

echo.
echo ==========================================
echo System Ready Status
echo ==========================================
echo.
echo Prerequisites:
echo ✓ Bloomberg Terminal should be running and logged in
echo.
echo If all items show ✓, your Bloomberg ChatGPT is ready!
echo If any show ✗, run start_bloomberg_broker.bat
echo.
pause

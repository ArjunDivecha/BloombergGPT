@echo off
title Stop Bloomberg Data Broker
echo ==========================================
echo Stopping Bloomberg Data Broker System
echo ==========================================
echo.

echo [1/3] Stopping Python processes (Bloomberg Broker)...
taskkill /F /IM python.exe /T 2>nul
if %errorlevel% == 0 (
    echo ✓ Bloomberg Broker stopped
) else (
    echo ℹ No Bloomberg Broker processes found
)

echo.
echo [2/3] Stopping ngrok processes...
taskkill /F /IM ngrok.exe /T 2>nul
if %errorlevel% == 0 (
    echo ✓ ngrok Tunnel stopped
) else (
    echo ℹ No ngrok processes found
)

echo.
echo [3/3] Checking for remaining processes...
netstat -ano | findstr :8000 >nul
if %errorlevel% == 0 (
    echo ⚠ Warning: Something is still using port 8000
    echo You may need to manually stop it
) else (
    echo ✓ Port 8000 is free
)

echo.
echo ==========================================
echo Bloomberg Data Broker System Stopped!
echo ==========================================
echo.
echo All processes have been terminated.
echo Bloomberg Terminal can continue running.
echo.
pause

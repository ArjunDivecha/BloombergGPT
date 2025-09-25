@echo off
title Bloomberg Data Broker - Environment Setup
echo ==========================================
echo Bloomberg Data Broker Environment Setup
echo ==========================================
echo.

echo This script installs Python dependencies, creates configuration files,
echo and adds desktop shortcuts for starting/stopping the system.
echo.
set /p CONTINUE="Continue with setup? (Y/N): "
if /I not "%CONTINUE%"=="Y" exit /b

echo.
echo [1/4] Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERR] Failed to install Python packages
    pause
    exit /b 1
)
echo [OK] Python dependencies installed

echo.
echo [2/4] Installing Bloomberg API Python bindings (if available)...
python -m pip install --index-url=https://blpapi.bloomberg.com/repository/releases/python/simple/ blpapi
if %errorlevel% neq 0 (
    echo [WARN] Bloomberg API installation failed (mock mode will be used)
) else (
    echo [OK] Bloomberg API installed
)

echo.
echo [3/4] Preparing .env configuration...
if not exist ".env" (
    if exist "env.template" (
        copy "env.template" ".env" >nul
        echo [OK] Created .env from env.template
        echo Please edit .env to set a secure API_KEY if needed.
    ) else (
        (
            echo API_KEY=Caeser00**
            echo BLOOMBERG_HOST=localhost
            echo BLOOMBERG_PORT=8194
            echo BROKER_HOST=0.0.0.0
            echo BROKER_PORT=8000
            echo RATE_LIMIT=60/minute
        )> .env
        echo [OK] Created .env with default settings
    )
) else (
    echo [INFO] Existing .env detected (leaving unchanged)
)

echo.
echo [4/4] Creating desktop shortcuts...
set VBS=create_shortcuts.vbs
(
    echo Set oWS = WScript.CreateObject("WScript.Shell")
    echo sLink = "%USERPROFILE%\Desktop\Start Bloomberg Broker.lnk"
    echo Set oLnk = oWS.CreateShortcut(sLink)
    echo oLnk.TargetPath = "%~dp0start_bloomberg_broker.bat"
    echo oLnk.WorkingDirectory = "%~dp0"
    echo oLnk.Description = "Start Bloomberg Data Broker"
    echo oLnk.Save
    echo sLink = "%USERPROFILE%\Desktop\Stop Bloomberg Broker.lnk"
    echo Set oLnk = oWS.CreateShortcut(sLink)
    echo oLnk.TargetPath = "%~dp0stop_bloomberg_broker.bat"
    echo oLnk.WorkingDirectory = "%~dp0"
    echo oLnk.Description = "Stop Bloomberg Data Broker"
    echo oLnk.Save
) > %VBS%

cscript %VBS% >nul 2>&1
del %VBS% >nul 2>&1
if exist "%USERPROFILE%\Desktop\Start Bloomberg Broker.lnk" (
    echo [OK] Desktop shortcuts created
) else (
    echo [WARN] Could not create desktop shortcuts
)

echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Ensure your Cloudflare tunnel config (cloudflared-broker.yml) is ready.
echo 2. Launch Bloomberg Terminal and log in.
echo 3. Use the desktop shortcut "Start Bloomberg Broker" to begin a session.
echo.
pause

@echo off
title Bloomberg Data Broker - Environment Setup
echo ==========================================
echo Bloomberg Data Broker Environment Setup
echo ==========================================
echo.

echo This script will set up your Bloomberg Data Broker environment.
echo.
echo Prerequisites:
echo - Python 3.8+ installed
echo - Bloomberg Terminal installed and running
echo - Internet connection for downloading packages
echo.
set /p continue="Continue with setup? (Y/N): "
if /i not "%continue%"=="Y" exit /b

echo.
echo [1/4] Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ✗ Failed to install Python dependencies
    pause
    exit /b 1
)
echo ✓ Python dependencies installed

echo.
echo [2/4] Installing Bloomberg API...
python -m pip install --index-url=https://blpapi.bloomberg.com/repository/releases/python/simple/ blpapi
if %errorlevel% neq 0 (
    echo ⚠ Bloomberg API installation failed
    echo This is normal if you don't have Bloomberg access
    echo The system will use mock data instead
) else (
    echo ✓ Bloomberg API installed
)

echo.
echo [2.5/4] Setting up configuration file...
if not exist ".env" (
    if exist "env.template" (
        copy "env.template" ".env" >nul
        echo ✓ Created .env from template
        echo ⚠ IMPORTANT: Edit .env file and add your NGROK_AUTHTOKEN
        echo   Get it from: https://dashboard.ngrok.com/get-started/your-authtoken
    ) else (
        echo API_KEY=Caeser00** > .env
        echo NGROK_AUTHTOKEN=your_ngrok_authtoken_here >> .env
        echo NGROK_REGION=us >> .env
        echo BLOOMBERG_HOST=localhost >> .env
        echo BLOOMBERG_PORT=8194 >> .env
        echo BROKER_HOST=0.0.0.0 >> .env
        echo BROKER_PORT=8000 >> .env
        echo RATE_LIMIT=60/minute >> .env
        echo ✓ Created .env with default settings
        echo ⚠ IMPORTANT: Edit .env file and add your NGROK_AUTHTOKEN
    )
) else (
    echo ℹ .env file already exists
)

echo.
echo [3/4] Testing Bloomberg connection...
python -c "
try:
    import blpapi
    sessionOptions = blpapi.SessionOptions()
    sessionOptions.setServerHost('localhost')
    sessionOptions.setServerPort(8194)
    session = blpapi.Session(sessionOptions)
    if session.start():
        print('✓ Bloomberg Terminal connection successful')
        session.stop()
    else:
        print('✗ Bloomberg Terminal connection failed')
        print('Make sure Bloomberg Terminal is running and logged in')
except ImportError:
    print('⚠ Bloomberg API not available - will use mock data')
except Exception as e:
    print('✗ Bloomberg connection error:', str(e))
"

echo.
echo [4/4] Creating desktop shortcuts...
echo Set oWS = WScript.CreateObject("WScript.Shell") > create_shortcuts.vbs
echo sLinkFile = "%USERPROFILE%\Desktop\Start Bloomberg Broker.lnk" >> create_shortcuts.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> create_shortcuts.vbs
echo oLink.TargetPath = "%~dp0start_bloomberg_broker.bat" >> create_shortcuts.vbs
echo oLink.WorkingDirectory = "%~dp0" >> create_shortcuts.vbs
echo oLink.Description = "Start Bloomberg Data Broker System" >> create_shortcuts.vbs
echo oLink.Save >> create_shortcuts.vbs

echo sLinkFile = "%USERPROFILE%\Desktop\Stop Bloomberg Broker.lnk" >> create_shortcuts.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> create_shortcuts.vbs
echo oLink.TargetPath = "%~dp0stop_bloomberg_broker.bat" >> create_shortcuts.vbs
echo oLink.WorkingDirectory = "%~dp0" >> create_shortcuts.vbs
echo oLink.Description = "Stop Bloomberg Data Broker System" >> create_shortcuts.vbs
echo oLink.Save >> create_shortcuts.vbs

cscript create_shortcuts.vbs >nul 2>&1
del create_shortcuts.vbs >nul 2>&1

if exist "%USERPROFILE%\Desktop\Start Bloomberg Broker.lnk" (
    echo ✓ Desktop shortcuts created
) else (
    echo ⚠ Could not create desktop shortcuts
)

echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Your Bloomberg Data Broker is ready to use!
echo.
echo Quick Start:
echo 1. Make sure Bloomberg Terminal is running and logged in
echo 2. Double-click "Start Bloomberg Broker" on your desktop
echo 3. Use your Bloomberg ChatGPT!
echo.
echo Files created:
echo - start_bloomberg_broker.bat (Start system)
echo - stop_bloomberg_broker.bat (Stop system)
echo - check_status.bat (Check system status)
echo - Desktop shortcuts for easy access
echo.
pause

@echo off
REM Opens a new PowerShell window and runs the test
start powershell -NoExit -Command "cd '\\Mac\Dropbox-1\AAA Backup\A Working\BloombergGPT'; Write-Host 'Running quick test...'; python quick_test.py; Write-Host '`n`nTest complete! You can close this window or run more tests.'"


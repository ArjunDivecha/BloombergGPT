@echo off
echo ================================================================================
echo Bloomberg Account Capability Test
echo ================================================================================
echo.
echo This will test what your Bloomberg account can access.
echo Make sure Bloomberg Terminal and broker are running!
echo.
echo Press any key to start...
pause > nul

cd /d "%~dp0"
python test_account_capabilities.py > test_output.txt 2>&1

echo.
echo ================================================================================
echo Test complete! 
echo.
echo Results saved to:
echo   - test_output.txt (full output)
echo   - account_capabilities_results.json (summary)
echo ================================================================================
echo.
echo Opening results file...
type test_output.txt
echo.
echo.
echo Press any key to exit...
pause > nul


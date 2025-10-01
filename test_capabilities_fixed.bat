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

REM Map UNC path to a drive letter temporarily
pushd "%~dp0"

python test_account_capabilities.py > test_output.txt 2>&1

echo.
echo ================================================================================
echo Test complete! 
echo ================================================================================
echo.
type test_output.txt
echo.
echo.
echo Results saved to test_output.txt
echo.
pause

popd


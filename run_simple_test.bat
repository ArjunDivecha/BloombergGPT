@echo off
echo Running simple Bloomberg capability test...
echo.

REM Map UNC path to drive letter
pushd "%~dp0"

python simple_test.py

echo.
echo ================================================================================
echo TEST RESULTS
echo ================================================================================
echo.
type test_results.txt

echo.
echo ================================================================================
echo Test complete!
echo ================================================================================
echo.
pause

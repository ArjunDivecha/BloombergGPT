@echo off
echo Running Bloomberg capability test from current directory...
echo.

REM Get current directory and run test
for %%I in ("%~dp0") do set "CURRENT_DIR=%%~fI"

echo Current directory: %CURRENT_DIR%
echo.

REM Run the test
python "%CURRENT_DIR%simple_test.py"

echo.
echo ================================================================================
echo TEST RESULTS
echo ================================================================================
echo.

type "%CURRENT_DIR%test_results.txt"

echo.
echo ================================================================================
echo Test complete!
echo ================================================================================
echo.
pause

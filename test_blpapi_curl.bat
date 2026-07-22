@echo off
echo Testing Bloomberg API via curl...
echo.
curl -X GET "http://localhost:8000/blp/refdata?ticker=AAPL&fields=PX_LAST&fields=NAME" -H "x-api-key: Caeser00**"
echo.
echo Test complete.

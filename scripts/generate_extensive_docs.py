"""
Script to Generate Extensive BLPAPI Documentation

This script creates a comprehensive set of documentation files to simulate
hundreds or thousands of data items for the RAG system.

INPUT FILES:
- None

OUTPUT FILES:
- docs/blpapi_docs_full/ - Directory with generated documentation files

Version History:
- Date: September 22, 2025
- Author: AI Assistant
- Changes: Initial creation to generate extensive docs
"""

import os

# Create directory structure
docs_dir = 'docs/blpapi_docs_full'
os.makedirs(docs_dir, exist_ok=True)

# Generate comprehensive field reference
field_reference = """
# Field Reference Guide

## Equity Fields
"""

equity_fields = [
    "PX_LAST", "PX_OPEN", "PX_HIGH", "PX_LOW", "PX_VOLUME", "MARKET_CAP", "DVD_EX_DT",
    "DVD_SH_DT", "CHG_PCT_1D", "CHG_PCT_1M", "PE_RATIO", "PB_RATIO", "EV_EBITDA",
    "FREE_CASH_FLOW", "RETURN_COM_EQY", "BETA", "VOLATILITY_30D", "VOLATILITY_90D",
    "TURNOVER", "AVG_VOLUME_30D", "AVG_VOLUME_90D", "SHARES_OUT", "FLOAT_SHARES",
    "INSTITUTIONAL_HOLDINGS_PCT", "SHORT_INTEREST", "DIVIDEND_YIELD", "DIVIDEND_RATE",
    "EARNINGS_PER_SHARE", "BOOK_VALUE_PER_SHARE", "CASH_PER_SHARE", "SALES_PER_SHARE",
    "RETURN_ON_EQUITY", "RETURN_ON_ASSETS", "RETURN_ON_INVESTED_CAPITAL",
    "GROSS_MARGIN", "OPERATING_MARGIN", "NET_MARGIN", "EBITDA_MARGIN",
    "CURRENT_RATIO", "QUICK_RATIO", "DEBT_TO_EQUITY", "INTEREST_COVERAGE",
    "CASH_FLOW_FROM_OPERATIONS", "CAPEX", "FREE_CASH_FLOW_YIELD", "PAYOUT_RATIO",
    "52_WEEK_HIGH", "52_WEEK_LOW", "50_DAY_MOVING_AVG", "200_DAY_MOVING_AVG",
    "BOLLINGER_UPPER", "BOLLINGER_LOWER", "RSI_14D", "MACD", "STOCHASTIC_K",
    "STOCHASTIC_D", "WILLIAMS_R", "CCI_14D", "ADX_14D", "MFI_14D", "OBV",
    "ACCUMULATION_DISTRIBUTION", "ATR_14D", "BOLLINGER_BANDWIDTH", "STANDARD_DEVIATION_20D"
]

for i, field in enumerate(equity_fields):
    field_reference += f"- {field}: Description for {field} - detailed explanation of what this field represents in Bloomberg data. This includes {i+1} specific details about usage, calculation method, and typical values.\n"

field_reference += """

## Index Fields
"""
index_fields = [
    "INDX_MWEIGHT", "INDX_MWEIGHT_PCT", "INDX_LEVEL", "INDX_VOLUME", "INDX_MCAP",
    "INDX_DIV_YIELD", "INDX_PE_RATIO", "INDX_PB_RATIO", "INDX_MEMBERS",
    "INDX_CHG_PCT_1D", "INDX_CHG_PCT_1M", "INDX_CHG_PCT_1Y", "INDX_VOLATILITY_30D",
    "INDX_VOLATILITY_90D", "INDX_BETA", "INDX_CORRELATION", "INDX_SHARPE_RATIO",
    "INDX_SORTINO_RATIO", "INDX_MAX_DRAWDOWN", "INDX_VALUE_AT_RISK", "INDX_TURNOVER",
    "INDX_ADVANCING", "INDX_DECLINING", "INDX_UNCHANGED", "INDX_NEW_HIGHS",
    "INDX_NEW_LOWS", "INDX_52W_HIGH", "INDX_52W_LOW", "INDX_WEIGHTED_AVG_MCAP",
    "INDX_FLOAT_ADJUSTED", "INDX_DIVIDEND_POINTS", "INDX_PRICE_RETURN",
    "INDX_TOTAL_RETURN", "INDX_GROSS_RETURN", "INDX_NET_RETURN", "INDX_CURRENCY_HEDGED"
]

for field in index_fields:
    field_reference += f"- {field}: Index field description for {field}\n"

field_reference += """

## Currency Fields
"""
currency_fields = [
    "EURUSD Curncy", "GBPUSD Curncy", "USDJPY Curncy", "AUDUSD Curncy", "USDCAD Curncy",
    "USDCHF Curncy", "NZDUSD Curncy", "USDNOK Curncy", "USDSEK Curncy", "USDMXN Curncy",
    "EURJPY Curncy", "EURGBP Curncy", "GBPJPY Curncy", "AUDJPY Curncy", "CADJPY Curncy",
    "CHFJPY Curncy", "EURCHF Curncy", "GBPCHF Curncy", "AUDCHF Curncy", "CADCHF Curncy",
    "EURCAD Curncy", "GBPCAD Curncy", "AUDCAD Curncy", "NZDCAD Curncy", "EURNZD Curncy",
    "GBPNZD Curncy", "AUDNZD Curncy", "EURSEK Curncy", "GBPSEK Curncy", "USDZAR Curncy",
    "EURZAR Curncy", "GBPZAR Curncy", "USDTRY Curncy", "EURTRY Curncy", "USDPLN Curncy",
    "EURPLN Curncy", "USDHUF Curncy", "EURHUF Curncy", "USDCZK Curncy", "EURCZK Curncy"
]

for field in currency_fields:
    field_reference += f"- {field}: Currency pair {field}\n"

# Continue with more content...

with open(f'{docs_dir}/field_reference_comprehensive.md', 'w') as f:
    f.write(field_reference)

print("Generated comprehensive field reference with many fields.")

# Generate ticker reference
ticker_reference = """
# Comprehensive Ticker Reference

## US Equity Tickers
"""

us_tickers = [
    "AAPL US Equity", "MSFT US Equity", "GOOGL US Equity", "AMZN US Equity", "TSLA US Equity",
    "META US Equity", "NVDA US Equity", "JPM US Equity", "JNJ US Equity", "V US Equity",
    "PG US Equity", "UNH US Equity", "HD US Equity", "MA US Equity", "DIS US Equity",
    "PYPL US Equity", "BAC US Equity", "ADBE US Equity", "CMCSA US Equity", "XOM US Equity"
]

for i, ticker in enumerate(us_tickers):
    ticker_reference += f"- {ticker}: Company {i+1} - {ticker}\n"

# Add many more tickers...
for i in range(100):  # Add 100 more
    ticker_reference += f"- TICKER{i:03d} US Equity: Example ticker {i+21}\n"

ticker_reference += """

## Index Tickers
"""
indices = ["SPX Index", "INDU Index", "VIX Index", "NDX Index", "RUT Index"]
for idx in indices:
    ticker_reference += f"- {idx}: Index ticker\n"

with open(f'{docs_dir}/ticker_reference_comprehensive.md', 'w') as f:
    f.write(ticker_reference)

print("Generated comprehensive ticker reference.")

# Generate API examples
api_examples = """
# BLPAPI Python Examples

## Reference Data Request Example
```python
import blpapi

session = blpapi.Session()
session.start()

service = session.getService("//blp/refdata")
request = service.createRequest("ReferenceDataRequest")

# Add securities
request.getElement("securities").appendValue("AAPL US Equity")
request.getElement("securities").appendValue("MSFT US Equity")

# Add fields
fields = request.getElement("fields")
fields.appendValue("PX_LAST")
fields.appendValue("MARKET_CAP")
fields.appendValue("DVD_EX_DT")
fields.appendValue("VOLUME")

session.sendRequest(request)
```

## Historical Data Request Example
```python
request = service.createRequest("HistoricalDataRequest")
request.getElement("securities").appendValue("SPX Index")
fields = request.getElement("fields")
fields.appendValue("PX_LAST")
fields.appendValue("VOLUME")

periodicity = request.getElement("periodicityAdjustment")
periodicity.setChoice("DAILY")

start_date = request.getElement("startDate")
start_date.setValue("20230101")

end_date = request.getElement("endDate")
end_date.setValue("20231231")

session.sendRequest(request)
```

## Error Handling
```python
try:
    response = session.nextEvent()
    if response.eventType() == blpapi.Event.RESPONSE:
        # Process response
        pass
except Exception as e:
    print(f"Error: {e}")
```

## Best Practices
1. Always check for response errors
2. Use appropriate overrides
3. Batch requests for efficiency
4. Handle session lifecycle properly
5. Use proper date formats
"""

for i in range(10):  # Create multiple example files
    with open(f'{docs_dir}/api_examples_{i+1}.md', 'w') as f:
        f.write(api_examples + f"\n\nAdditional examples for section {i+1}")

print("Generated multiple API example files.")

print("Extensive documentation generation complete!")

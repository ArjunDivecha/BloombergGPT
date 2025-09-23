# BLPAPI Python Developer Guide

## Overview
BLPAPI (Bloomberg API) for Python provides access to Bloomberg's data and services.

## Key Concepts
- **Sessions**: Used to connect to Bloomberg services
- **Services**: Represent Bloomberg data services like reference data
- **Requests**: Used to query data
- **Responses**: Contain the data returned

## Basic Usage
```python
import blpapi

session = blpapi.Session()
session.start()

service = session.getService("//blp/refdata")
request = service.createRequest("ReferenceDataRequest")
```

## Field Mappings
- PX_LAST: Last traded price
- DVD_EX_DT: Dividend ex-date
- MARKET_CAP: Market capitalization
- VOLUME: Trading volume

## Error Handling
Always check for errors in responses:
```python
if response.hasElement("responseError"):
    print("Error in response")
```

## Historical Data
Use HistoricalDataRequest for time series data:
- Specify date ranges
- Choose periodicity (daily, monthly, etc.)
- Handle adjustments for splits/dividends

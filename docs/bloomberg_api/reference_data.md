# Reference Data Service

## ReferenceDataRequest
Used for snapshot data queries.

### Required Parameters
- securities: List of tickers
- fields: List of field mnemonics

### Example Fields
- PX_LAST: Last price
- DVD_EX_DT: Dividend ex-date
- MARKET_CAP: Market cap
- VOLUME: Daily volume
- CHG_PCT_1D: 1-day price change %

### Response Structure
The response contains data organized by security and field.

## ReferenceDataResponse
Contains the actual data points for each requested field.

## Error Handling
Check for responseError elements in the response.

## Performance Tips
- Batch requests for multiple securities
- Use appropriate overrides for specific data

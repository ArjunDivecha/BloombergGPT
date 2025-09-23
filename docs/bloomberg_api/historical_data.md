# Historical Data Service

## HistoricalDataRequest
Used for time series data queries.

### Parameters
- securities: List of tickers
- fields: List of field mnemonics
- startDate: Start date for data
- endDate: End date for data
- periodicity: Data frequency (DAILY, MONTHLY, etc.)

### Available Fields
- PX_LAST: Historical prices
- VOLUME: Historical volumes
- CHG_PCT_1D: Daily price changes
- MARKET_CAP: Historical market caps

### Date Formats
- YYYYMMDD format
- Relative dates supported

### Response Structure
Data is returned as time series for each security/field combination.

## Adjustments
- PRICE_ADJ: For corporate actions
- CAPITAL_CHANGES: For splits/dividends

## Performance Considerations
- Limit date ranges for faster queries
- Use appropriate periodicity

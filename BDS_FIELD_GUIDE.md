# Bloomberg Bulk Data (BDS) Field Guide

## Overview

**BDS (Bulk Data Service)** fields return **multi-row tabular data** instead of single values. These fields provide access to historical records, segment breakdowns, ownership details, and other array-based datasets from Bloomberg.

### What's Different About BDS?

| Feature | BDP (Reference Data) | BDS (Bulk Data) |
|---------|---------------------|-----------------|
| **Returns** | Single value | Array/table of values |
| **Example** | `PX_LAST = 254.63` | 94 dividend records with dates & amounts |
| **Use Case** | Current snapshot | Historical analysis, detailed breakdowns |
| **Endpoint** | `/blp/refdata` | `/blp/bulkdata` |

---

## Using BDS Fields

### API Endpoint

```
GET /blp/bulkdata?ticker=AAPL&field=DVD_HIST_ALL
```

### Response Format

```json
{
  "ticker": "AAPL",
  "field": "DVD_HIST_ALL",
  "field_info": {
    "id": "DV030",
    "name": "DVD_HIST_ALL",
    "description": "Dividend History - All"
  },
  "row_count": 94,
  "data": [
    {
      "Declared Date": "2025-07-31",
      "Ex-Date": "2025-08-11",
      "Record Date": "2025-08-11",
      "Payable Date": "2025-08-14",
      "Dividend Amount": "0.260000",
      "Dividend Frequency": "Quarter",
      "Dividend Type": "Regular Cash"
    },
    ...
  ],
  "provenance": "Source: Bloomberg (brokered via Desktop API) — fields: [DVD_HIST_ALL] — retrieved at 2025-10-01 12:34:56 UTC"
}
```

---

## Comprehensive BDS Field Catalog

Based on analysis of **3,144 Bloomberg fields**, we identified **530+ potential BDS fields**. Below are the most useful categories:

### 1. Dividend History (✅ Tested & Working)

| Field ID | Display Name | Description | Example Use Case |
|----------|--------------|-------------|------------------|
| **DV030** | `DVD_HIST_ALL` | **Dividend History - All** | Complete dividend timeline with all types |
| **DV029** | `DVD_HIST` | **Dividend History - Cash** | Cash dividends only (most common) |
| **DV037** | `EQY_DVD_HIST_GROSS` | **Dividend History (Gross) - All** | Gross dividends (before tax) |
| **DV031** | `EQY_DVD_HIST_SPLITS` | **Dividend History - Splits** | Stock split history |
| **DV158** | `DVD_HIST_GROSS_WITH_AMT_STAT` | **Dividend History (Gross) - With Amount Status** | Includes payment status flags |
| **DV157** | `DVD_HIST_ALL_WITH_AMT_STATUS` | **Dividend History - All (With Amount Status)** | All dividends with status |
| **DV156** | `DVD_HIST_WITH_AMT_STATUS` | **Dividend History - Cash (With Amount Status)** | Cash dividends with status |

**Tested with:** `AAPL US Equity` - Returns 94 dividend records (1987-2025)

**Sample Data Columns:**
- `Declared Date` - When dividend was announced
- `Ex-Date` - Last date to own stock to receive dividend
- `Record Date` - Date to be on record to receive dividend
- `Payable Date` - Payment date
- `Dividend Amount` - Amount per share
- `Dividend Frequency` - Quarter, Annual, Special, etc.
- `Dividend Type` - Regular Cash, Special, etc.

---

### 2. Earnings History

| Field ID | Display Name | Description | Example Use Case |
|----------|--------------|-------------|------------------|
| **DY895** | `EARN_ANN_DT_TIME_HIST_WITH_EPS` | **Earnings Announcement Date & Time History with EPS** | Track earnings surprises over time |
| **RX079** | `EARN_YLD_HIST` | **Earnings Yield** | Historical earnings yield data |

**Use Case Example:**
```
GET /blp/bulkdata?ticker=MSFT&field=EARN_ANN_DT_TIME_HIST_WITH_EPS
```
Returns historical earnings announcements with:
- Announcement date & time
- Reported EPS
- Expected EPS
- Surprise %

---

### 3. Stock Splits (🔍 To Be Tested)

| Field ID | Display Name | Description |
|----------|--------------|-------------|
| **DV031** | `EQY_DVD_HIST_SPLITS` | **Dividend History - Splits** |

**Expected Data:**
- Split date
- Split ratio (e.g., 2-for-1)
- Adjustment factor

---

### 4. Revenue & Segment Breakdowns (🔍 To Be Tested)

| Field ID | Display Name | Description |
|----------|--------------|-------------|
| **PG667** | `PG_REVENUE_VALUE` | **Product/Geographic Revenue Value** |
| **PG679** | `PG_GROSS_PROFIT_VALUE` | **Product/Geographic Gross Profit Value** |
| **PG870** | `PG_COST_OF_REVENUE_VALUE` | **Product/Geographic Cost of Revenue Value** |
| **PG775** | `PG_GROSS_MARGIN_VALUE` | **Product/Geographic Gross Margin Value** |
| **PG791** | `PG_SALES_1_YR_GROWTH_VALUE` | **Product/Geographic Sales - 1 Year Growth Value** |

**Use Case:**
```
GET /blp/bulkdata?ticker=GOOGL&field=PG_REVENUE_VALUE
```
Expected to return revenue broken down by:
- Product line (e.g., Search, YouTube, Cloud)
- Geographic region (Americas, EMEA, APAC)
- Time period

---

### 5. Cash Flow Details (🔍 To Be Tested)

| Field ID | Display Name | Description |
|----------|--------------|-------------|
| **CF026** | `CF_DVD_PAID` | **Dividends Paid** |
| **CF017** | `CF_CAP_EXPEND_PRPTY_ADD` | **Capital Expenditures/Prop Add** |
| **CF025** | `CF_CASH_FROM_INV_ACT` | **Cash from Investing Activities** |
| **CF027** | `CF_INCR_ST_BORROW` | **Inc(Dec) in ST Borrowings** |

**Note:** These may be single-value fields rather than bulk. Testing required.

---

### 6. Ownership & Holdings (🔍 To Be Tested)

| Field ID | Display Name | Description |
|----------|--------------|-------------|
| **DZ611** | `HISTORICAL_HOLDERS` | **Historical Holders** |
| **DS210** | `EQY_INST_SH_HELD` | **Instit Owner # of Shares Held** |
| **DS211** | `EQY_INST_PCT_SH_OUT` | **Instit Owner % Shares Out** |
| **DS209** | `EQY_INST_HOLD` | **Instit Owner # of Holders** |
| **DS207** | `EQY_INST_BUYS` | **Instit Owner # of Buyers** |
| **DS208** | `EQY_INST_SELLS` | **Instit Owner # of Sellers** |

**Likely Returns:**
- Institutional holder name
- Shares held
- % of outstanding
- Change from previous period

---

### 7. Index Composition (🔍 To Be Tested)

| Field ID | Display Name | Description |
|----------|--------------|-------------|
| **DS184** | `INDX_MWEIGHT_HIST` | **Index Members Weights - Historical** |

**Use Case:**
```
GET /blp/bulkdata?ticker=SPX&field=INDX_MWEIGHT_HIST
```
Could return historical constituent weights for S&P 500.

---

### 8. Historical Market Metrics (🔍 To Be Tested)

| Field ID | Display Name | Description |
|----------|--------------|-------------|
| **RR250** | `HISTORICAL_MARKET_CAP` | **Historical Market Cap** |
| **RT081-RT085** | `HIST_TRR_PREV_1YR` to `HIST_TRR_PREV_5YR` | **Historical Total Return** |
| **RT024** | `HIST_TRR_MONTHLY` | **Historical Monthly Total Return** |

---

### 9. Implied Volatility History (🔍 To Be Tested)

| Field ID | Display Name | Description |
|----------|--------------|-------------|
| **RK074** | `HIST_CALL_IMP_VOL` | **Hist. Call Implied Volatility** |
| **RK075** | `HIST_PUT_IMP_VOL` | **Hist. Put Implied Volatility** |

---

### 10. Stock Buyback History (🔍 To Be Tested)

| Field ID | Display Name | Description |
|----------|--------------|-------------|
| **DZ328** | `STOCK_BUYBACK_HISTORY` | **Stock Buyback History** |

**Expected Returns:**
- Buyback announcement date
- Shares repurchased
- Average price paid
- Remaining authorization

---

## Field Naming Conventions

Bloomberg uses prefixes to categorize fields:

| Prefix | Category | Example |
|--------|----------|---------|
| `DV` | Dividend | `DV030` (DVD_HIST_ALL) |
| `DY` | Derived/Yield | `DY895` (Earnings History) |
| `PG` | Product/Geographic | `PG667` (Revenue by Segment) |
| `CF` | Cash Flow | `CF026` (Dividends Paid) |
| `DS` | Dataset/Security | `DS184` (Index Weights) |
| `DZ` | Data/Misc | `DZ611` (Historical Holders) |
| `RR` | Ratio/Return | `RR250` (Historical Market Cap) |
| `RT` | Return | `RT024` (Monthly Total Return) |
| `RK` | Risk | `RK074` (Call Implied Vol) |
| `RX` | Ratios Extended | `RX079` (Earnings Yield) |
| `BH` | Bulk Header | `BH390` (Dividend Bulk Header) |

---

## Testing Strategy

### Priority 1: Core Financial History (✅ DV030 Working)
- [x] **DV030** - Dividend History (CONFIRMED WORKING)
- [ ] **DY895** - Earnings History
- [ ] **DV031** - Stock Splits
- [ ] **DZ328** - Buyback History

### Priority 2: Segment Analysis
- [ ] **PG667** - Revenue by Product/Geography
- [ ] **PG679** - Gross Profit Breakdown
- [ ] **PG775** - Gross Margin by Segment

### Priority 3: Ownership & Holdings
- [ ] **DZ611** - Historical Holders
- [ ] **DS210-DS211** - Institutional Ownership

### Priority 4: Market Metrics
- [ ] **RR250** - Historical Market Cap
- [ ] **RT024** - Monthly Total Returns
- [ ] **DS184** - Index Weights History

---

## Testing Guide

### Test Template

```bash
# Test a new BDS field
curl -X GET "http://localhost:8000/blp/bulkdata?ticker=AAPL&field=<FIELD_ID>" \
     -H "X-API-Key: Caeser00**"
```

### Good Test Tickers

| Ticker | Why Good for Testing |
|--------|----------------------|
| `AAPL` | Mature company, long history |
| `MSFT` | Multiple business segments |
| `GOOGL` | Complex product lines |
| `JPM` | Financial sector complexity |
| `SPX` | Index with constituents |

### Expected Behaviors

**Success (HTTP 200):**
- Returns `row_count > 0`
- `data` is an array of objects
- Each row has multiple fields

**Non-Bulk Field (HTTP 400):**
- Error: "Field is not a bulk data field"
- Happens when you try BDS on a BDP field

**No Data (HTTP 404):**
- Returns empty data array or error
- May mean the security doesn't have that data type

---

## Known Limitations

### 1. Not All Fields Return Bulk Data
Some fields that sound like they should be bulk (e.g., `CF_FREE_CASH_FLOW`) might actually be single-value BDP fields.

### 2. Field Availability Varies by Security Type
- Equity-specific fields won't work on commodities
- Index fields won't work on individual stocks
- Check field documentation for applicability

### 3. Historical Depth Varies
- Some companies have limited historical data
- Newly public companies have shorter histories
- Some fields only go back a few years

### 4. Data Quality
- Bloomberg may have `NaN` values for incomplete data (now sanitized to `null`)
- Some historical data may be restated
- Always check `Amount Status` fields when available

---

## Common Use Cases

### 1. Dividend Analysis
```
Field: DV030 (DVD_HIST_ALL)
Ticker: AAPL, KO, JNJ (high-quality dividend payers)
Analysis: Dividend growth rate, consistency, yield trends
```

### 2. Earnings Surprise Analysis
```
Field: DY895 (EARN_ANN_DT_TIME_HIST_WITH_EPS)
Ticker: Tech stocks (AAPL, MSFT, GOOGL, AMZN)
Analysis: Beat/miss patterns, surprise correlation with stock moves
```

### 3. Business Segment Performance
```
Field: PG667 (PG_REVENUE_VALUE)
Ticker: GOOGL, MSFT, AMZN (diversified businesses)
Analysis: Which segments are growing fastest
```

### 4. Ownership Trends
```
Field: DZ611 (HISTORICAL_HOLDERS)
Ticker: Any equity
Analysis: Institutional accumulation/distribution
```

### 5. Stock Split History
```
Field: DV031 (EQY_DVD_HIST_SPLITS)
Ticker: AAPL, TSLA, NVDA (have split recently)
Analysis: Pre/post-split performance
```

---

## API Response Size Management

### Automatic Handling
The broker automatically:
1. **Sanitizes NaN values** to `null` for JSON compliance
2. **Converts dates** to strings (YYYY-MM-DD format)
3. **Limits response size** to prevent timeout issues

### If You Get Too Much Data
Some bulk fields may return thousands of rows. To handle this:

1. **Use more specific fields** (e.g., `DVD_HIST` instead of `DVD_HIST_ALL_WITH_AMT_STATUS`)
2. **Filter on the client side** after receiving data
3. **Consider using BDH** (historical data endpoint) with date ranges instead

---

## Bloomberg Field Catalog

**Total Fields Analyzed:** 3,144  
**Identified Bulk (BDS) Fields:** 530+  
**Tested & Working:** 1 (DV030)  
**Ready for Testing:** 25+ high-value fields

### Full Field List Available In:
- `Production Data/Comprehensive_Bulk_Fields.xlsx` - All 530 potential BDS fields
- `Production Data/Curated_BDS_Fields.xlsx` - Top priority fields for testing
- `Production Data/Bloomberg Master Field List.xlsx` - Complete field catalog

---

## Next Steps

1. **Test Priority 1 Fields** (Earnings, Splits, Buybacks)
2. **Validate Revenue Segment Fields** (PG667, PG679)
3. **Test Ownership Fields** (DZ611, DS210)
4. **Document Field-Specific Column Names** for each tested field
5. **Create Field Matrix** showing which fields work for which security types

---

## Support

For questions about specific BDS fields:
1. Check the Bloomberg Terminal documentation (`FLDS <GO>`)
2. Test the field using the `/blp/bulkdata` endpoint
3. Review the comprehensive field list Excel files
4. Contact Bloomberg support for field-specific questions

---

**Last Updated:** October 1, 2025  
**Version:** 1.0  
**Status:** ✅ DV030 (Dividend History) Confirmed Working | 🔍 25+ Fields Ready for Testing


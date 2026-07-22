# Bloomberg Field Quick Reference

## ✅ VERIFIED WORKING FIELDS

### Basic Market Data
- `PX_LAST` - Last/Current Price
- `PX_OPEN` - Opening Price
- `PX_HIGH` - Daily High
- `PX_LOW` - Daily Low
- `CHG_PCT_1D` - 1-Day % Change
- `VOLUME` - Trading Volume
- `PX_VOLUME` - Same as VOLUME

### Valuation Metrics
- `CUR_MKT_CAP` - Current Market Cap
- `PE_RATIO` - P/E Ratio (Trailing)
- `PX_TO_BOOK_RATIO` - Price/Book Ratio
- `EV_TO_T12M_EBITDA` - EV/EBITDA

### Dividends
- `DVD_YILD` - Dividend Yield (NOTE: YILD not YIELD)
- `DVD_SH_LAST` - Last Dividend per Share
- `DVD_PAYOUT_RATIO` - Payout Ratio

### Fundamentals
- `BEST_EPS` - Consensus EPS Estimate
- `TRAIL_12M_EPS` - Trailing 12M EPS
- `IS_EPS` - EPS from Income Statement
- `RETURN_COM_EQY` - Return on Equity (ROE)
- `RETURN_ON_ASSET` - Return on Assets (ROA)

### Balance Sheet
- `TOT_DEBT_TO_TOT_EQY` - Debt/Equity Ratio
- `CUR_RATIO` - Current Ratio
- `CASH_AND_MARKETABLE_SECURITIES` - Cash & Equivalents

### Moving Averages & Technical
- `MOV_AVG_50D` - 50-Day Moving Average
- `MOV_AVG_200D` - 200-Day Moving Average
- `VOLATILITY_90D` - 90-Day Volatility
- `BETA_ADJ_OVERRIDABLE` - Beta

### Company Info
- `NAME` - Company Name
- `COUNTRY_ISO` - Country Code
- `INDUSTRY_SECTOR` - Sector
- `GICS_SECTOR_NAME` - GICS Sector

---

## 🔍 HOW TO FIND FIELDS

### If you need a field but don't know the exact name:

1. **Search by concept:**
```
GET /blp/fields/search?query=dividend yield&limit=10
→ Returns: DVD_YILD, DVD_YIELD_*, etc.
```

2. **Search by category:**
```
GET /blp/fields/search?query=earnings&limit=20
→ Returns: All earnings-related fields
```

3. **Common search terms:**
- "price" → PX_LAST, PX_OPEN, PX_HIGH, etc.
- "market cap" → CUR_MKT_CAP
- "P/E" or "PE ratio" → PE_RATIO
- "dividend" → DVD_YILD, DVD_HIST_ALL, etc.
- "EPS" → BEST_EPS, TRAIL_12M_EPS, etc.
- "revenue" → SALES_REV_TURN, PG_REVENUE (bulk)
- "debt" → TOT_DEBT_TO_TOT_EQY, TOTAL_DEBT
- "cash" → CASH_AND_MARKETABLE_SECURITIES

---

## ⚠️ BULK DATA FIELDS (Use /blp/bulkdata)

These return tables/arrays, not single values:

- `DVD_HIST_ALL` - Complete dividend history
- `PG_REVENUE` - Revenue by segment
- `TOP_20_HOLDERS_PUBLIC_FILINGS` - Major shareholders
- `EARN_ANN_DT_TIME_HIST_WITH_EPS` - Earnings announcements
- `CF_FREE_CASH_FLOW` - Cash flow by period

---

## ❌ FIELDS THAT DON'T EXIST (Common Mistakes)

- `PRICE` → Use `PX_LAST`
- `MARKET_CAP` → Use `CUR_MKT_CAP`
- `DVD_YIELD` → Use `DVD_YILD` (note spelling)
- `P_E_RATIO` → Use `PE_RATIO`
- `RSI` or `MACD` → Not available as simple fields
- `EPS_FWD` → Use `BEST_EPS`

---

## 📊 SNAPSHOT ENDPOINT DEFAULT FIELDS

The `/blp/snapshot` endpoint returns these 6 fields automatically:
1. `PX_LAST` - Price
2. `CHG_PCT_1D` - Daily Change %
3. `VOLUME` - Volume
4. `CUR_MKT_CAP` - Market Cap
5. `PE_RATIO` - P/E Ratio
6. `DVD_YILD` - Dividend Yield

**Use this for quick market snapshots!**

---

## 🎯 STRATEGY FOR UNKNOWN FIELDS

1. **Try the obvious name first** (e.g., PX_LAST for price)
2. **If that fails, search:** `/blp/fields/search?query=concept`
3. **Use the closest match** from search results
4. **For complex metrics (RSI, MACD):** These may not exist as simple fields

**Don't ask user - just search and use what you find!**



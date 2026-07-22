# Bloomberg BDS Fields - Quick Reference Card

## 🚀 Most Useful BDS Fields

### ✅ CONFIRMED WORKING

```bash
# Dividend History (TESTED with AAPL - Returns 94 records)
GET /blp/bulkdata?ticker=AAPL&field=DV030
```

**Field:** `DV030` - `DVD_HIST_ALL`  
**Returns:** Complete dividend history with dates, amounts, frequencies, types  
**Sample Tickers:** AAPL, KO, JNJ, PG, T  

---

### 🔥 HIGH PRIORITY - TEST NEXT

#### 1. Earnings History
```bash
GET /blp/bulkdata?ticker=AAPL&field=DY895
```
**Field:** `DY895` - `EARN_ANN_DT_TIME_HIST_WITH_EPS`  
**Returns:** Earnings announcements with reported EPS, expected EPS, surprises  
**Best For:** Tech stocks (AAPL, MSFT, GOOGL, AMZN, NVDA)

#### 2. Stock Split History
```bash
GET /blp/bulkdata?ticker=AAPL&field=DV031
```
**Field:** `DV031` - `EQY_DVD_HIST_SPLITS`  
**Returns:** Historical stock splits with dates and ratios  
**Best For:** AAPL, TSLA, NVDA, AMZN (companies that have split)

#### 3. Revenue by Segment
```bash
GET /blp/bulkdata?ticker=GOOGL&field=PG667
```
**Field:** `PG667` - `PG_REVENUE_VALUE`  
**Returns:** Revenue breakdown by product line and geography  
**Best For:** Diversified companies (GOOGL, MSFT, AMZN, JNJ, PG)

#### 4. Stock Buyback History
```bash
GET /blp/bulkdata?ticker=AAPL&field=DZ328
```
**Field:** `DZ328` - `STOCK_BUYBACK_HISTORY`  
**Returns:** Historical buyback programs with amounts and dates  
**Best For:** AAPL, MSFT, JPM, BAC, WFC

#### 5. Institutional Ownership History
```bash
GET /blp/bulkdata?ticker=TSLA&field=DZ611
```
**Field:** `DZ611` - `HISTORICAL_HOLDERS`  
**Returns:** Ownership changes over time by institution  
**Best For:** High institutional interest stocks (TSLA, NVDA, AAPL)

---

## 📊 By Category

### Dividend Fields
| Field ID | Name | What It Returns |
|----------|------|-----------------|
| **DV030** ✅ | `DVD_HIST_ALL` | All dividend types |
| **DV029** | `DVD_HIST` | Cash dividends only |
| **DV037** | `EQY_DVD_HIST_GROSS` | Gross (pre-tax) dividends |
| **DV031** | `EQY_DVD_HIST_SPLITS` | Stock splits |

### Earnings Fields
| Field ID | Name | What It Returns |
|----------|------|-----------------|
| **DY895** 🔥 | `EARN_ANN_DT_TIME_HIST_WITH_EPS` | Earnings announcements & EPS |
| **RX079** | `EARN_YLD_HIST` | Earnings yield history |

### Revenue/Segment Fields
| Field ID | Name | What It Returns |
|----------|------|-----------------|
| **PG667** 🔥 | `PG_REVENUE_VALUE` | Revenue by product/geography |
| **PG679** | `PG_GROSS_PROFIT_VALUE` | Gross profit by segment |
| **PG775** | `PG_GROSS_MARGIN_VALUE` | Margins by segment |
| **PG791** | `PG_SALES_1_YR_GROWTH_VALUE` | Growth rates by segment |

### Ownership Fields
| Field ID | Name | What It Returns |
|----------|------|-----------------|
| **DZ611** 🔥 | `HISTORICAL_HOLDERS` | Historical ownership changes |
| **DS210** | `EQY_INST_SH_HELD` | Institutional shares held |
| **DS211** | `EQY_INST_PCT_SH_OUT` | % owned by institutions |
| **DS209** | `EQY_INST_HOLD` | Number of institutional holders |
| **DS207** | `EQY_INST_BUYS` | New institutional buyers |
| **DS208** | `EQY_INST_SELLS` | Institutional sellers |

### Corporate Actions
| Field ID | Name | What It Returns |
|----------|------|-----------------|
| **DV031** 🔥 | `EQY_DVD_HIST_SPLITS` | Stock split history |
| **DZ328** 🔥 | `STOCK_BUYBACK_HISTORY` | Share repurchase history |

### Market Metrics
| Field ID | Name | What It Returns |
|----------|------|-----------------|
| **RR250** | `HISTORICAL_MARKET_CAP` | Market cap over time |
| **RT024** | `HIST_TRR_MONTHLY` | Monthly total returns |
| **RT081** | `HIST_TRR_PREV_1YR` | 1-year historical total return |

### Index Data
| Field ID | Name | What It Returns |
|----------|------|-----------------|
| **DS184** | `INDX_MWEIGHT_HIST` | Historical index weights |

---

## 🎯 Best Test Tickers by Category

| Category | Recommended Tickers | Why |
|----------|---------------------|-----|
| **Dividends** | AAPL, KO, JNJ, PG, T | Long dividend history |
| **Earnings** | AAPL, MSFT, GOOGL, AMZN, NVDA | Quarterly reporters with surprises |
| **Segments** | GOOGL, MSFT, AMZN, JNJ, PG | Diversified business lines |
| **Buybacks** | AAPL, MSFT, JPM, BAC | Active buyback programs |
| **Ownership** | TSLA, NVDA, GME, AMC | High institutional activity |
| **Splits** | AAPL, TSLA, NVDA, AMZN | Recent stock splits |
| **Index** | SPX, INDU, NDX | Major indices |

---

## 💡 Usage Examples

### Example 1: Find Dividend Growth Stocks
```bash
# Get complete dividend history
curl "http://localhost:8000/blp/bulkdata?ticker=KO&field=DV030" \
     -H "X-API-Key: Caeser00**"

# Analyze the data for:
# - Consecutive years of increases
# - Average growth rate
# - Dividend consistency
```

### Example 2: Earnings Surprise Analysis
```bash
# Get earnings history with EPS
curl "http://localhost:8000/blp/bulkdata?ticker=AAPL&field=DY895" \
     -H "X-API-Key: Caeser00**"

# Calculate:
# - Beat/miss rate
# - Average surprise %
# - Correlation with stock price moves
```

### Example 3: Segment Performance
```bash
# Get revenue by product/geography
curl "http://localhost:8000/blp/bulkdata?ticker=GOOGL&field=PG667" \
     -H "X-API-Key: Caeser00**"

# Identify:
# - Fastest growing segments
# - Geographic exposure
# - Revenue concentration
```

### Example 4: Buyback Analysis
```bash
# Get stock buyback history
curl "http://localhost:8000/blp/bulkdata?ticker=AAPL&field=DZ328" \
     -H "X-API-Key: Caeser00**"

# Track:
# - Total capital returned
# - Average buyback price vs. current
# - Buyback timing (opportunistic vs. consistent)
```

### Example 5: Institutional Flow
```bash
# Get historical holders
curl "http://localhost:8000/blp/bulkdata?ticker=TSLA&field=DZ611" \
     -H "X-API-Key: Caeser00**"

# Monitor:
# - New institutional buyers
# - Institutional selloffs
# - Smart money positioning
```

---

## ⚡ Quick Test Commands

```bash
# Set your API key (run once per session)
export API_KEY="Caeser00**"

# Test template
curl -H "X-API-Key: $API_KEY" \
     "http://localhost:8000/blp/bulkdata?ticker=<TICKER>&field=<FIELD_ID>"

# Quick tests
curl -H "X-API-Key: $API_KEY" "http://localhost:8000/blp/bulkdata?ticker=AAPL&field=DV030"  # Dividends ✅
curl -H "X-API-Key: $API_KEY" "http://localhost:8000/blp/bulkdata?ticker=AAPL&field=DY895"  # Earnings 🔥
curl -H "X-API-Key: $API_KEY" "http://localhost:8000/blp/bulkdata?ticker=AAPL&field=DV031"  # Splits 🔥
curl -H "X-API-Key: $API_KEY" "http://localhost:8000/blp/bulkdata?ticker=GOOGL&field=PG667" # Revenue 🔥
curl -H "X-API-Key: $API_KEY" "http://localhost:8000/blp/bulkdata?ticker=AAPL&field=DZ328"  # Buybacks 🔥
```

---

## 📝 Response Format

All BDS endpoints return:
```json
{
  "ticker": "AAPL",
  "field": "DV030",
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
      "Payable Date": "2025-08-14",
      "Dividend Amount": "0.260000",
      "Dividend Frequency": "Quarter",
      "Dividend Type": "Regular Cash"
    }
  ],
  "provenance": "Source: Bloomberg..."
}
```

---

## 🔍 Troubleshooting

### HTTP 400 - Field is not a bulk data field
**Cause:** You're trying to use a BDP (single-value) field with the BDS endpoint  
**Solution:** Use `/blp/refdata` instead for single-value fields

### HTTP 404 - No bulk data returned
**Cause:** The security doesn't have data for that field  
**Solution:** Try a different ticker or verify the field applies to that security type

### HTTP 500 - Internal server error
**Cause:** Usually NaN values or data parsing issues  
**Solution:** This is now handled automatically - report if it persists

### Empty data array
**Cause:** No historical data available for that security/field  
**Solution:** Normal for newly public companies or inapplicable fields

---

## 📚 Full Documentation

- **Comprehensive Guide:** `BDS_FIELD_GUIDE.md` - All 530+ fields
- **Comparison:** `BDS_COMPARISON_SUMMARY.md` - What you requested vs. what exists
- **Field Catalog:** `Production Data/Comprehensive_Bulk_Fields.xlsx` - Full list
- **Curated List:** `Production Data/Curated_BDS_Fields.xlsx` - Top priority fields

---

**Version:** 1.0  
**Last Updated:** October 1, 2025  
**Status:** ✅ 1 Confirmed Working | 🔥 5 High Priority Ready | 🔍 525+ To Explore



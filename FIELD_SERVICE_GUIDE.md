# Bloomberg Field Service Guide

## Overview

The Bloomberg Data Broker now includes **three powerful field discovery endpoints** that provide programmatic access to Bloomberg's live field catalog via the `//blp/apiflds` service. These endpoints enable dynamic field search, detailed metadata retrieval, and complete catalog browsing.

## Why Use Field Service Endpoints?

### The Problem
Bloomberg has **24,000+ data fields** across equities, bonds, commodities, currencies, and derivatives. Finding the right field for your analysis can be challenging:
- Field names aren't always intuitive (e.g., `DVD_YILD` for dividend yield)
- Documentation may not be readily accessible
- You might not know what fields exist for a specific data category

### The Solution
These endpoints let you:
- **Discover fields by keyword** - Search "dividend" to find all dividend-related fields
- **Get complete documentation** - View full descriptions, data types, and available overrides
- **Browse entire catalog** - List all Static or RealTime fields available to you
- **Validate field names** - Confirm exact mnemonics before making data requests

---

## Endpoints

### 1. `/blp/fields/search` - Keyword Field Search

**Purpose:** Find Bloomberg fields by searching keywords or phrases

**Use Cases:**
- "What fields are available for earnings data?"
- "Show me all dividend-related fields"
- "Find fields containing 'market cap'"

**Request:**
```bash
GET /blp/fields/search?query=dividend&limit=20&api_key=YOUR_KEY
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search keyword or phrase |
| `limit` | integer | No | 50 | Max results (1-500) |
| `api_key` | string | Yes | - | Your API key |

**Response:**
```json
{
  "query": "dividend",
  "total_results": 47,
  "limit": 20,
  "results": [
    {
      "mnemonic": "DVD_YILD",
      "id": "DY042",
      "description": "Dividend Yield",
      "datatype": "Double",
      "category": "Fundamental",
      "field_type": "Static"
    },
    {
      "mnemonic": "DVD_HIST_ALL",
      "id": "DH001",
      "description": "Dividend History All",
      "datatype": "Bulk",
      "category": "Fundamental",
      "field_type": "Static"
    }
  ],
  "provenance": "Bloomberg Field Search - query: 'dividend' - retrieved at 2025-10-01 14:30:00 UTC"
}
```

**Example Use Cases:**

```bash
# Find earnings fields
curl -H "x-api-key: YOUR_KEY" \
  "http://localhost:8000/blp/fields/search?query=earnings&limit=30"

# Find market cap fields
curl -H "x-api-key: YOUR_KEY" \
  "http://localhost:8000/blp/fields/search?query=market%20cap"

# Find P/E ratio fields
curl -H "x-api-key: YOUR_KEY" \
  "http://localhost:8000/blp/fields/search?query=P/E%20ratio&limit=10"

# Find revenue breakdown fields
curl -H "x-api-key: YOUR_KEY" \
  "http://localhost:8000/blp/fields/search?query=revenue%20segment"
```

---

### 2. `/blp/fields/info` - Detailed Field Information

**Purpose:** Get comprehensive metadata for specific Bloomberg fields

**Use Cases:**
- "What's the exact definition of LAST_PRICE?"
- "What data type does CUR_MKT_CAP return?"
- "What overrides are available for PX_VOLUME?"

**Request:**
```bash
GET /blp/fields/info?fields=LAST_PRICE,CUR_MKT_CAP,DVD_YILD&api_key=YOUR_KEY
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `fields` | string | Yes | Comma-separated field mnemonics |
| `api_key` | string | Yes | Your API key |

**Response:**
```json
{
  "fields": ["LAST_PRICE", "CUR_MKT_CAP", "DVD_YILD"],
  "results": [
    {
      "mnemonic": "LAST_PRICE",
      "id": "PR005",
      "description": "Last Trade/Last Price",
      "datatype": "Double",
      "category": "Market Activity",
      "field_type": "RealTime",
      "documentation": "The last price at which the security traded during regular market hours. For end-of-day data, this represents the closing price.",
      "overrides": [
        {
          "name": "EQY_FUND_CRNCY",
          "description": "Currency override for pricing"
        }
      ]
    },
    {
      "mnemonic": "CUR_MKT_CAP",
      "id": "MK001",
      "description": "Current Market Capitalization",
      "datatype": "Double",
      "category": "Fundamental",
      "field_type": "Static",
      "documentation": "Total market value of all outstanding shares. Calculated as current price × total shares outstanding.",
      "overrides": []
    },
    {
      "mnemonic": "DVD_YILD",
      "id": "DY042",
      "description": "Dividend Yield",
      "datatype": "Double",
      "category": "Fundamental",
      "field_type": "Static",
      "documentation": "Annual dividend per share divided by current stock price, expressed as a percentage.",
      "overrides": []
    }
  ],
  "provenance": "Bloomberg Field Info - fields: LAST_PRICE, CUR_MKT_CAP, DVD_YILD - retrieved at 2025-10-01 14:30:00 UTC"
}
```

**Example Use Cases:**

```bash
# Get info for a single field
curl -H "x-api-key: YOUR_KEY" \
  "http://localhost:8000/blp/fields/info?fields=LAST_PRICE"

# Get info for multiple fields at once
curl -H "x-api-key: YOUR_KEY" \
  "http://localhost:8000/blp/fields/info?fields=PE_RATIO,PX_TO_BOOK_RATIO,DVD_YILD"

# Verify bulk data fields
curl -H "x-api-key: YOUR_KEY" \
  "http://localhost:8000/blp/fields/info?fields=DVD_HIST_ALL,PG_REVENUE,TOP_20_HOLDERS_PUBLIC_FILINGS"
```

**Field Not Found Example:**
```json
{
  "fields": ["INVALID_FIELD"],
  "results": [
    {
      "id": "INVALID_FIELD",
      "error": "Field not found"
    }
  ],
  "provenance": "..."
}
```

---

### 3. `/blp/fields/list` - Complete Field Catalog

**Purpose:** Retrieve Bloomberg's entire field catalog, filtered by type

**Use Cases:**
- "Show me all Static (reference) fields"
- "List all RealTime (market data) fields"
- "Give me the complete field catalog"

**Request:**
```bash
GET /blp/fields/list?field_type=Static&limit=500&api_key=YOUR_KEY
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `field_type` | string | No | All | Field type filter: `All`, `Static`, or `RealTime` |
| `limit` | integer | No | 1000 | Max results (1-10,000) |
| `api_key` | string | Yes | - | Your API key |

**Field Types:**
- **`All`** - All available fields (Static + RealTime)
- **`Static`** - Reference/fundamental data (company info, financials, ratings, etc.)
- **`RealTime`** - Live market data (prices, quotes, volume, bids/asks, etc.)

**Response:**
```json
{
  "field_type": "Static",
  "total_returned": 500,
  "limit": 500,
  "note": "Results may be truncated if limit reached",
  "results": [
    {
      "mnemonic": "NAME",
      "id": "DS002",
      "description": "Name of the security",
      "datatype": "String",
      "category": "Descriptive",
      "field_type": "Static"
    },
    {
      "mnemonic": "CUR_MKT_CAP",
      "id": "MK001",
      "description": "Current Market Capitalization",
      "datatype": "Double",
      "category": "Fundamental",
      "field_type": "Static"
    }
    // ... 498 more fields
  ],
  "provenance": "Bloomberg Field List - type: Static - retrieved at 2025-10-01 14:30:00 UTC"
}
```

**Example Use Cases:**

```bash
# Get first 100 fields of all types
curl -H "x-api-key: YOUR_KEY" \
  "http://localhost:8000/blp/fields/list?field_type=All&limit=100"

# Get all Static (reference) fields
curl -H "x-api-key: YOUR_KEY" \
  "http://localhost:8000/blp/fields/list?field_type=Static&limit=5000"

# Get RealTime market data fields
curl -H "x-api-key: YOUR_KEY" \
  "http://localhost:8000/blp/fields/list?field_type=RealTime&limit=200"

# Get maximum fields (10,000)
curl -H "x-api-key: YOUR_KEY" \
  "http://localhost:8000/blp/fields/list?field_type=All&limit=10000"
```

**Warning:** 
- Large requests (limit > 1000) may take 10-30 seconds to complete
- Bloomberg Terminal must be running and connected
- Results are capped at the limit you specify

---

## Workflow Examples

### Example 1: Discovering Dividend Fields

**Goal:** Find all dividend-related fields, then get detailed info

```bash
# Step 1: Search for dividend fields
curl -H "x-api-key: YOUR_KEY" \
  "http://localhost:8000/blp/fields/search?query=dividend&limit=50"

# Returns: DVD_YILD, DVD_HIST_ALL, DVD_PAY_DT, etc.

# Step 2: Get detailed info for top 3 fields
curl -H "x-api-key: YOUR_KEY" \
  "http://localhost:8000/blp/fields/info?fields=DVD_YILD,DVD_HIST_ALL,DVD_PAY_DT"

# Step 3: Use the bulk field to get actual data
curl -H "x-api-key: YOUR_KEY" \
  "http://localhost:8000/blp/bulkdata?ticker=AAPL&field=DVD_HIST_ALL"
```

---

### Example 2: Finding P/E Ratio Field

**Goal:** Determine the exact field name for P/E ratio

```bash
# Step 1: Search for P/E fields
curl -H "x-api-key: YOUR_KEY" \
  "http://localhost:8000/blp/fields/search?query=P/E%20ratio&limit=10"

# Returns: PE_RATIO, BEST_PE_RATIO, HISTORICAL_PE_RATIO, etc.

# Step 2: Get info to see which one you need
curl -H "x-api-key: YOUR_KEY" \
  "http://localhost:8000/blp/fields/info?fields=PE_RATIO,BEST_PE_RATIO"

# Step 3: Use the correct field in your data request
curl -H "x-api-key: YOUR_KEY" \
  "http://localhost:8000/blp/refdata?ticker=AAPL&fields=PE_RATIO,CUR_MKT_CAP"
```

---

### Example 3: Exploring All Bulk Data Fields

**Goal:** Find all available bulk (array/table) data fields

```bash
# Search for bulk fields
curl -H "x-api-key: YOUR_KEY" \
  "http://localhost:8000/blp/fields/search?query=history&limit=100"

# Look for fields with datatype: "Bulk" in the results
# Common bulk fields: DVD_HIST_ALL, EARN_ANN_*, PG_REVENUE, TOP_20_HOLDERS_*

# Get detailed documentation
curl -H "x-api-key: YOUR_KEY" \
  "http://localhost:8000/blp/fields/info?fields=DVD_HIST_ALL,PG_REVENUE"
```

---

## Data Types Reference

Bloomberg fields return different data types:

| Data Type | Description | Example Fields |
|-----------|-------------|----------------|
| **String** | Text values | NAME, TICKER, COUNTRY |
| **Double** | Decimal numbers | LAST_PRICE, CUR_MKT_CAP, DVD_YILD |
| **Integer** | Whole numbers | VOLUME, NUM_EMPLOYEES |
| **Date** | Date values | DVD_PAY_DT, EARN_ANN_DT |
| **Boolean** | True/False | IS_EPS, HAS_DIVIDEND |
| **Bulk** | Array/table data | DVD_HIST_ALL, PG_REVENUE |
| **Sequence** | Nested structures | Complex multi-level data |

---

## Best Practices

### 1. Start with Search, Then Get Info
```bash
# GOOD: First search to discover, then get details
/blp/fields/search?query=earnings
/blp/fields/info?fields=BEST_EPS,TRAIL_12M_EPS

# AVOID: Guessing field names
/blp/refdata?ticker=AAPL&fields=EARNINGS  # Might not exist
```

### 2. Use Appropriate Limits
```bash
# GOOD: Reasonable limits for exploration
/blp/fields/search?query=dividend&limit=50

# AVOID: Unnecessarily high limits
/blp/fields/search?query=a&limit=500  # Too broad
```

### 3. Validate Field Names Before Data Requests
```bash
# GOOD: Verify field exists and is correct type
/blp/fields/info?fields=DVD_HIST_ALL
# Confirms it's a Bulk field, then:
/blp/bulkdata?ticker=AAPL&field=DVD_HIST_ALL

# AVOID: Requesting data without validation
/blp/bulkdata?ticker=AAPL&field=DIVIDEND_HISTORY  # Field doesn't exist
```

### 4. Cache Field Catalog Locally
```bash
# Get complete catalog once per day
/blp/fields/list?field_type=All&limit=10000
# Save results to local database/file
# Use cached data for field validation
```

---

## Comparison: Field Service vs. Master Field List

| Feature | Field Service Endpoints | Bloomberg Master Field List.xlsx |
|---------|------------------------|----------------------------------|
| **Data Source** | Live Bloomberg catalog | Curated static list |
| **Total Fields** | 24,000+ available | 3,674 curated fields |
| **Updates** | Always current | Manual updates |
| **Search** | Dynamic keyword search | Excel filter/search |
| **Documentation** | Full Bloomberg docs | Custom annotations |
| **Custom Notes** | No | Yes |
| **Offline Access** | No (requires Bloomberg) | Yes |
| **Programmatic Access** | Yes (API) | No (manual file) |
| **Best For** | Discovery & validation | Quick reference & production use |

**Recommendation:** Use both together:
- **Field Service**: Discover new fields, validate names, get latest definitions
- **Master List**: Quick reference for your most-used fields with custom notes

---

## Error Handling

### Common Errors

**503 Service Unavailable**
```json
{
  "detail": "Bloomberg API not available"
}
```
**Solution:** Ensure Bloomberg Terminal is running and logged in

**503 Service Unavailable**
```json
{
  "detail": "Could not open //blp/apiflds service"
}
```
**Solution:** Bloomberg session issue - restart terminal or check connection

**400 Bad Request** (Field Info)
```json
{
  "detail": "No valid fields provided"
}
```
**Solution:** Provide at least one field in comma-separated format

**401 Unauthorized**
```json
{
  "detail": "Invalid API key"
}
```
**Solution:** Check your API key is correct in the `x-api-key` header

---

## Rate Limiting

All Field Service endpoints are subject to the same rate limits as other broker endpoints:

- **60 requests per minute** per API key
- Rate limit applies across all endpoints
- Exceeding limit returns `429 Too Many Requests`

**Tip:** For bulk catalog downloads, use high limits (e.g., `limit=10000`) in a single request rather than multiple smaller requests.

---

## Technical Details

### Bloomberg Service Used
- Service: `//blp/apiflds`
- Requires: Bloomberg Desktop API connection
- Timeout: 5-10 seconds depending on request type

### Request Types
1. **FieldSearchRequest** - Keyword search
2. **FieldInfoRequest** - Detailed field metadata
3. **FieldListRequest** - Complete catalog retrieval

### Session Management
- Uses the same Bloomberg session as data requests
- Session pooling enabled for performance
- Thread-safe session access

---

## Quick Reference Card

```bash
# Field Discovery Workflow
# 1. Search by keyword
curl -H "x-api-key: YOUR_KEY" \
  "http://localhost:8000/blp/fields/search?query=YOUR_KEYWORD&limit=50"

# 2. Get detailed info
curl -H "x-api-key: YOUR_KEY" \
  "http://localhost:8000/blp/fields/info?fields=FIELD1,FIELD2,FIELD3"

# 3. Use field in data request
curl -H "x-api-key: YOUR_KEY" \
  "http://localhost:8000/blp/refdata?ticker=AAPL&fields=FIELD1,FIELD2"

# Browse Complete Catalog
curl -H "x-api-key: YOUR_KEY" \
  "http://localhost:8000/blp/fields/list?field_type=Static&limit=1000"
```

---

## Next Steps

1. **Test the endpoints** with common searches (dividend, earnings, market cap)
2. **Build a field catalog cache** by running `/blp/fields/list` periodically
3. **Integrate with your workflow** - use search before making data requests
4. **Update your Master List** - add newly discovered fields to your Excel catalog

**For more examples, see:**
- `BDS_FIELD_GUIDE.md` - Comprehensive bulk data field reference
- `BEQS_SCREENING_GUIDE.md` - Bloomberg Equity Screening guide
- `README.md` - Main Bloomberg Data Broker documentation

---

**Version:** 2.2.0 (October 1, 2025)
**Author:** Bloomberg Data Broker Team


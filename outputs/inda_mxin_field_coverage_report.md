# Bloomberg Field Coverage Report: INDA Equity & MXIN Index

**Test Date:** 2026-04-29 15:48:55  
**Securities Tested:** INDA Equity, MXIN Index  
**Total Fields Tested:** 43

## Summary

| Security | Successful | Failed | Success Rate |
|----------|-----------|--------|--------------|
| INDA Equity | 4 | 39 | 9.3% |
| MXIN Index | 13 | 30 | 30.2% |

---

## INDA Equity (iShares India ETF) Results

### Successful Fields (4)
- **EQY_REC_CONS**: 0.000000
- **TOT_BUY_REC**: 0
- **TOT_HOLD_REC**: 0
- **TOT_SELL_REC**: 0

*Note: All recommendation fields show 0, likely because ETFs don't have analyst coverage like individual stocks.*

### Failed Fields (39)
All other fields returned null. This is expected for an ETF as:
- Forward consensus fields (BEST_*) typically apply to individual stocks, not ETFs
- Revision signals require analyst coverage
- Margin/quality fields are company-specific

---

## MXIN Index (Mexico Index) Results

### Successful Fields (13)

#### 1. Forward Consensus Levels (8/15 successful)
- **BEST_EPS**: 136.642837 ✓
- **BEST_EPS_NEXT_YR**: null ✗
- **BEST_EPS_2YR**: null ✗
- **BEST_EPS_3YR**: null ✗
- **BEST_SALES**: 1219.145381 ✓
- **BEST_SALES_NEXT_YR**: null ✗
- **BEST_EBITDA**: 234.817922 ✓
- **BEST_EBIT**: 183.605062 ✓
- **BEST_NET_INCOME**: null ✗
- **BEST_DIV_YLD**: 1.488928 ✓
- **BEST_DPS**: 43.482982 ✓
- **BEST_TARGET_PRICE**: 3380.317957 ✓
- **BEST_LTG_EPS**: 10.410611 ✓
- **BEST_CAPEX**: -106.848719 ✓
- **BEST_BPS**: 925.832578 ✓

#### 2. Revision Signals (1/12 successful)
- **EARN_REV_UP_NUM_BROKERS_1M**: null ✗
- **EARN_REV_UP_NUM_BROKERS_3M**: null ✗
- **EARN_REV_DN_NUM_BROKERS_1M**: null ✗
- **EARN_REV_DN_NUM_BROKERS_3M**: null ✗
- **EARN_REV_NUM_BROKERS_1M**: null ✗
- **EARN_REV_NUM_BROKERS_3M**: null ✗
- **BEST_EPS_3MO_PCT_CHG**: -1.383584 ✓
- **BEST_EPS_1MO_PCT_CHG**: null ✗
- **BEST_SALES_3MO_PCT_CHG**: null ✗
- **BEST_TARGET_PRICE_PCT_CHG_1M**: null ✗
- **BEST_TARGET_PRICE_PCT_CHG_3M**: null ✗

#### 3. Dispersion and Conviction (0/4 successful)
- **BEST_EPS_STDEV**: null ✗
- **BEST_EPS_HIGH**: null ✗
- **BEST_EPS_LOW**: null ✗
- **BEST_EPS_NUMEST**: null ✗

#### 4. Earnings Surprise / Beat-Miss (0/3 successful)
- **EARN_SURPRISE_PCT**: null ✗
- **EARN_BEAT_RATE_LAST_4Q**: null ✗
- **EPS_ESTIMATE_VS_REPORTED**: null ✗

#### 5. Recommendation Revisions (0/5 successful)
- **EQY_REC_CONS**: null ✗
- **TOT_BUY_REC**: null ✗
- **TOT_HOLD_REC**: null ✗
- **TOT_SELL_REC**: null ✗
- **BEST_ANALYST_RECS_BULLISH_PCT**: null ✗

#### 6. Margin and Quality Revisions (3/5 successful)
- **BEST_OPP_MARGIN**: null ✗
- **BEST_NET_MARGIN**: null ✗
- **BEST_ROE**: 14.278345 ✓
- **BEST_ROA**: 2.435070 ✓
- **BEST_ROIC**: null ✗

---

## Key Findings

### 1. Field Name Verification Needed
Many fields from the item.md instructions returned null. This could be due to:
- Bloomberg field mnemonics drifting over time (as noted in item.md)
- Fields not available at index level for MXIN
- Fields requiring specific overrides or request parameters

### 2. MXIN Index Coverage
MXIN Index has reasonable coverage for:
- Basic forward consensus (EPS, Sales, EBITDA, EBIT, Dividend, etc.)
- One revision signal (BEST_EPS_3MO_PCT_CHG)
- Some quality metrics (ROE, ROA)

However, it lacks coverage for:
- Multi-year forward estimates (FY2, FY3, FY4)
- Detailed revision broker counts
- Dispersion metrics (STDEV, HIGH, LOW, NUMEST)
- Earnings surprise data
- Recommendation data

### 3. INDA Equity Limitations
INDA Equity (an ETF) has minimal analyst coverage. Only basic recommendation fields returned data (all zeros). This is expected behavior for ETFs.

---

## Recommendations

1. **Verify Field Names**: Use Bloomberg's FLDS<GO> to verify the correct mnemonics for the failed fields
2. **Test on Major Indices**: As suggested in item.md, test on SPX or NKY which likely have better coverage
3. **Fallback to Constituent Aggregation**: For fields that don't work at index level, pull from constituents and aggregate
4. **Check Coverage Thresholds**: Gate derived signals on minimum coverage (e.g., require BEST_EPS_NUMEST >= 5)
5. **Test Alternative Field Names**: Some fields may have different mnemonics (e.g., EPS_ESTIMATE instead of BEST_EPS)

---

## Next Steps

1. Run the same test on a major index (SPX Index) to establish a baseline
2. Use Bloomberg field search to find correct mnemonics for failed fields
3. Implement fallback logic for fields requiring constituent aggregation
4. Add coverage quality checks before using signals in production

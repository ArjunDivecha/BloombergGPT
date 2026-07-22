Here's the comprehensive list, organized by what each signal captures. I want to flag upfront: Bloomberg field mnemonics drift over time and not all stock-level fields aggregate cleanly to your country index tickers (MXBR, MXIN, SPX, etc.). For country indices specifically, some of these come back directly from Bloomberg's index-level aggregation; others you'd need to pull at the constituent level and aggregate yourself. **Verify each field in FLDS\<GO\> before wiring it in** — I'll mark the ones I'm most confident work at index level vs. need-aggregation.

---

**1. Forward consensus levels (the inputs you already pull, expanded)**

Confident at index level:
- `BEST_EPS` — current FY1 consensus EPS *(you have)*
- `BEST_EPS_NEXT_YR` / `BEST_EPS_2YR` / `BEST_EPS_3YR` — FY2, FY3, FY4
- `BEST_SALES` / `BEST_SALES_NEXT_YR`
- `BEST_EBITDA` / `BEST_EBIT`
- `BEST_NET_INCOME`
- `BEST_DIV_YLD` *(you have via different name)*
- `BEST_DPS` — dividend per share consensus
- `BEST_TARGET_PRICE` — aggregated price target (very strong signal at country level)
- `BEST_LTG_EPS` *(you have as `LT Growth`)*
- `BEST_CAPEX`
- `BEST_BPS` — book per share

---

**2. Revision signals — direct fields**

These are the ones you specifically asked about. Confidence varies; verify per index.

- `EARN_REV_UP_NUM_BROKERS_1M` / `_3M` — count of brokers revising up
- `EARN_REV_DN_NUM_BROKERS_1M` / `_3M` — count revising down
- `EARN_REV_NUM_BROKERS_1M` / `_3M` — total brokers active
- `BEST_EPS_3MO_PCT_CHG` — % change in consensus over 3M (the cleanest direct revision field)
- `BEST_EPS_1MO_PCT_CHG` — 1M revision
- `BEST_SALES_3MO_PCT_CHG` — sales revision
- `BEST_TARGET_PRICE_PCT_CHG_1M` / `_3M`

If any of these fail at index level (some do for the more obscure indices), the **fallback method that always works**: pull `BEST_EPS` as a monthly time series via BDH, then compute the revision ratio yourself: `(BEST_EPS[t] / BEST_EPS[t-1]) - 1`. Cleaner anyway, because you control the lag and can compute breadth/dispersion consistently.

---

**3. Dispersion and conviction (orthogonal alpha)**

Revision *direction* is one signal; revision *agreement* is another. Stocks/countries with rising EPS *and* falling dispersion outperform those with rising EPS but widening dispersion (analysts disagreeing).

- `BEST_EPS_STDEV` — std dev of analyst estimates (raw dispersion)
- `BEST_EPS_HIGH` / `BEST_EPS_LOW` — top and bottom of estimate range
- `BEST_EPS_NUMEST` — number of estimates (coverage proxy)
- Derived: `BEST_EPS_STDEV / BEST_EPS` = coefficient of variation = normalized dispersion

---

**4. Earnings surprise / beat-miss (post-event signal)**

Country-level beat rates are predictive of next-quarter returns:
- `EARN_SURPRISE_PCT` — last reported surprise %
- `EARN_BEAT_RATE_LAST_4Q` — beat rate over trailing 4Q
- `EPS_ESTIMATE_VS_REPORTED` — most recent reported vs. consensus

For country indices, you'd typically aggregate from constituents — pull surprises per stock, weight by market cap, get country-level beat rate.

---

**5. Recommendation revisions (analyst conviction)**

Less predictive than EPS revisions but a useful confirming signal:
- `EQY_REC_CONS` — consensus recommendation (1=buy, 5=sell)
- `TOT_BUY_REC` / `TOT_HOLD_REC` / `TOT_SELL_REC` — counts
- `BEST_ANALYST_RECS_BULLISH_PCT` — % bullish

Index-level aggregation: cap-weighted average recommendation across constituents.

---

**6. Margin and quality revisions (often missed)**

- `BEST_OPP_MARGIN` — forward operating margin
- `BEST_NET_MARGIN`
- `BEST_ROE` *(you have)*
- `BEST_ROA`
- `BEST_ROIC` — return on invested capital, forward

The revision in **forward margin** is a particularly clean signal — it strips out volume/topline effects and isolates whether analysts think the firms can convert revenue to profit. Margin revisions are documented to outperform pure EPS revisions in some studies (because EPS conflates buybacks, share count, and operating performance).

---

**7. Construction approach for your panel**

Given you already pull `BEST_EPS`, `BEST_PE`, `BEST_ROE`, the minimum-effort additions to add to T2 Master are:

| Variable | Field | Frequency | Notes |
|---|---|---|---|
| EPS Revision 1M | `BEST_EPS_1MO_PCT_CHG` | Monthly | Direct |
| EPS Revision 3M | `BEST_EPS_3MO_PCT_CHG` | Monthly | Direct |
| Revision Breadth | derived: `(UP - DOWN) / TOTAL` | Monthly | From `EARN_REV_UP_NUM_BROKERS_3M` etc. |
| Estimate Dispersion | `BEST_EPS_STDEV / BEST_EPS` | Monthly | Coefficient of variation |
| Sales Revision 3M | `BEST_SALES_3MO_PCT_CHG` | Monthly | Topline revision |
| Forward Margin | `BEST_OPP_MARGIN` | Monthly | Pull level; T2 normalizes |
| Target Price Revision | `BEST_TARGET_PRICE_PCT_CHG_3M` | Monthly | Aggregated price target |
| LTG Revision | derived: `BEST_LTG_EPS[t] - BEST_LTG_EPS[t-3]` | Monthly | Long-term EPS growth revision |
| Beat Rate L4Q | aggregate from constituents | Quarterly | Actual vs. consensus history |
| Recommendation Consensus | `EQY_REC_CONS` | Monthly | 1-5 scale |

That's 10 new variables → 20 new sheets after `_CS` and `_TS` normalization through Step Two. Slots cleanly into your existing pipeline with no architecture change.

---

**8. The one thing to validate before pulling**

Before you build the BDH calls, run a quick FLDS test on **one** of your hardest-to-cover indices — probably Vietnam (`VNINDEX Index`?) or Philippines (`PCOMP Index`) — for each of the revision fields above. If the index-level field returns null, you know you need to fall back to the constituent-aggregate method for that variable. The big indices (SPX, NKY, MXBR, MXIN) will almost certainly support all of these directly.

The biggest risk with revisions data on EM indices is **stale/sparse coverage** — if `BEST_EPS_NUMEST` is below ~5 brokers for a country, the revision signal becomes noisy and dispersion becomes undefined. Worth gating your derived signals on a minimum-coverage threshold (e.g., set to NaN if fewer than 5 estimates).

Want me to draft the actual `xbbg` BDH call to pull all of these for the 34 country indices, with the right adjustment flags and a coverage-quality check?
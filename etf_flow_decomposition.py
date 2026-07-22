"""
ETF Country-Flow Decomposition for ASADO / T2
==============================================

Decomposes monthly net flows into the 34 T2 country indices by ETF tier:

  Tier 1: Passive cap-weighted              (sticky / forced flow)
  Tier 2: Smart beta rules-based             (factor-tilted retail/advisor)
  Tier 3: Active discretionary               (rare in ETF wrappers)
  Tier 4: Thematic / concentrated / hedged   (story money)
  Tier 5: Leveraged / inverse                (tactical traders, contrarian)

Output: monthly panel [date, country, tier, flow_usd, aum_usd] feeding
six derived T2 variables that go through Step Two normalization (_CS, _TS).

INPUT/OUTPUT FILES
==================
INPUT FILES:
  - etf_master_list.csv (manually curated, refresh quarterly)

OUTPUT FILES (under ./etf_decomp_output/):
  - etf_timeseries.parquet         Daily shares-out, NAV, AUM per ETF
  - etf_holdings.parquet           Monthly holdings snapshots, country-mapped
  - etf_flows_raw.parquet          Monthly flow USD per ETF
  - etf_country_tier_panel.parquet Decomposed (date, country, tier) flow panel
  - etf_signals_t2.csv             Six derived T2 variables, ready for Step Two

VERSION: 0.1 - initial scaffold
DATE:    2026-04-29

CRITICAL CAVEATS - READ BEFORE FIRST RUN
========================================
1. Bloomberg field mnemonics in CONFIG below MUST be verified in FLDS<GO>.
   The Desktop API field names are stable but issuer-specific edge cases exist.
2. ADR mapping: COUNTRY_OF_RISK is the right field for home-country exposure.
   Use COUNTRY_OF_INCORPORATION as fallback only when CO_RISK is null.
3. China A vs H requires exchange-code logic (Shanghai/Shenzhen -> ChinaA,
   HKEX -> ChinaH). Bloomberg's 2-letter country code "CN" is ambiguous.
4. Coverage: meaningful EM ETF history starts ~2003 (EEM launch). Smart beta
   really begins 2010+. Gate signals on minimum AUM thresholds.
5. ETF survivorship: pull data even for closed ETFs - they had real flow
   during their life that affects backtests.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import sys

# Add OpusBloomberg to path for Bloomberg API access
OPUS_BLOOMBERG_DIR = "/Users/arjundivecha/Dropbox/AAA Backup/A Working/OpusBloomberg"
if OPUS_BLOOMBERG_DIR not in sys.path:
    sys.path.insert(0, OPUS_BLOOMBERG_DIR)

# Import OpusBloomberg BBG module
try:
    from bbg import BBG, bloomberg_setup
    BLOOMBERG_AVAILABLE = True
except ImportError:
    BLOOMBERG_AVAILABLE = False
    print("Warning: OpusBloomberg bbg module not found. Using mock data for development/testing.")
    print("To use real Bloomberg data, ensure OpusBloomberg directory is available.")


def debug(message: str) -> None:
    """Emit debug output."""
    print(f"[DEBUG] {message}")

# ============================================================================
# CONFIG - VERIFY ALL BBG FIELD NAMES IN FLDS<GO> BEFORE RUNNING
# ============================================================================

BBG_SHARES_OUT = "EQY_SH_OUT"  # daily creations/redemptions effect
BBG_NAV        = "FUND_NET_ASSET_VAL"             # daily NAV (use NAV not market price)
BBG_AUM        = "FUND_TOTAL_ASSETS"              # total AUM USD
BBG_HOLDINGS   = "FUND_HOLDINGS"                  # BDS bulk holdings field
BBG_HOLD_DATE  = "FUND_HOLDINGS_AS_OF_DT"         # as-of date for holdings
# Fallbacks if any of the above fail at index/ETF level:
#   shares_out -> SHARES_OUTSTANDING, EQY_SH_OUT
#   nav        -> PX_LAST (uses market price, includes premium/discount noise)
#   holdings   -> PORTFOLIO_DATA (older field) or issuer-direct CSV download

START_DATE = "2003-01-01"   # EEM launch month
END_DATE: Optional[str] = None  # None = today

# Coverage thresholds - signals NaN'd below these to avoid spurious values
MIN_TIER_AUM_USD       = 200_000_000    # tier-level AUM per country-month
MIN_COUNTRY_TOTAL_AUM  = 500_000_000    # country total AUM per month
MIN_TIER1_ETF_COUNT    = 2              # need >= 2 tier-1 ETFs for sticky share

OUTPUT_DIR = Path("etf_decomp_output")

# ============================================================================
# THE 34 T2 COUNTRIES + REGIONAL FALLBACK WEIGHTS
# ============================================================================

T2_COUNTRIES = [
    "Australia", "Canada", "Denmark", "France", "Germany", "Hong Kong",
    "Italy", "Japan", "Netherlands", "Singapore", "Spain", "Sweden",
    "Switzerland", "U.K.", "U.S.", "NASDAQ", "US SmallCap",
    "Brazil", "Chile", "ChinaA", "ChinaH", "India", "Indonesia",
    "Korea", "Malaysia", "Mexico", "Philippines", "Poland",
    "Saudi Arabia", "South Africa", "Taiwan", "Thailand", "Turkey", "Vietnam",
]

# Static fallback country weights for regional ETFs (~ Q1 2026 MSCI weights).
# Use these only when actual holdings unavailable. Production: derive from
# pulled holdings panels via map_holdings_to_country() below.
REGIONAL_FALLBACK_WEIGHTS = {
    "REGIONAL_EM": {  # MSCI EM
        "ChinaH": 0.27, "ChinaA": 0.05, "India": 0.19, "Taiwan": 0.18,
        "Korea": 0.11, "Brazil": 0.04, "South Africa": 0.03,
        "Saudi Arabia": 0.03, "Mexico": 0.02, "Thailand": 0.02,
        "Indonesia": 0.02, "Malaysia": 0.01, "Poland": 0.01,
        "Philippines": 0.005, "Turkey": 0.005, "Chile": 0.005,
    },
    "REGIONAL_EM_EX_CHINA": {  # MSCI EM ex-China, renormalized
        "India": 0.26, "Taiwan": 0.25, "Korea": 0.15, "Brazil": 0.06,
        "South Africa": 0.04, "Saudi Arabia": 0.04, "Mexico": 0.03,
        "Thailand": 0.03, "Indonesia": 0.03, "Malaysia": 0.02,
        "Poland": 0.015, "Philippines": 0.007, "Turkey": 0.007,
        "Chile": 0.007,
    },
    "REGIONAL_DM_EX_US": {  # MSCI EAFE
        "Japan": 0.22, "U.K.": 0.16, "France": 0.11, "Switzerland": 0.10,
        "Germany": 0.09, "Australia": 0.07, "Netherlands": 0.04,
        "Sweden": 0.03, "Denmark": 0.03, "Italy": 0.03, "Spain": 0.03,
        "Hong Kong": 0.02, "Singapore": 0.01,
    },
    "REGIONAL_GLOBAL_EX_US": {  # ACWI ex-US: ~ DM 75% + EM 25%
        # Approximation - in production derive from holdings
        "Japan": 0.14, "U.K.": 0.10, "France": 0.07, "Switzerland": 0.06,
        "Germany": 0.06, "Australia": 0.04, "Canada": 0.07,
        "ChinaH": 0.07, "India": 0.05, "Taiwan": 0.05, "Korea": 0.03,
        "Netherlands": 0.025, "Brazil": 0.01, "Sweden": 0.02,
        "Hong Kong": 0.015, "Italy": 0.02, "Spain": 0.02, "Denmark": 0.02,
    },
    "REGIONAL_ASIA_EX_JAPAN": {
        "ChinaH": 0.34, "ChinaA": 0.06, "India": 0.22, "Taiwan": 0.20,
        "Korea": 0.13, "Hong Kong": 0.03, "Singapore": 0.015,
        "Thailand": 0.005,
    },
    "REGIONAL_ASEAN": {
        "Singapore": 0.32, "Thailand": 0.22, "Indonesia": 0.20,
        "Malaysia": 0.18, "Philippines": 0.07, "Vietnam": 0.01,
    },
    "REGIONAL_EUROZONE": {
        "France": 0.34, "Germany": 0.27, "Netherlands": 0.13,
        "Italy": 0.09, "Spain": 0.09, "Ireland": 0.04, "Belgium": 0.025,
    },
    "REGIONAL_EUROPE": {
        "U.K.": 0.24, "France": 0.17, "Switzerland": 0.16, "Germany": 0.14,
        "Netherlands": 0.07, "Sweden": 0.05, "Italy": 0.045, "Spain": 0.045,
        "Denmark": 0.04,
    },
    "REGIONAL_LATAM": {
        "Brazil": 0.55, "Mexico": 0.31, "Chile": 0.07, "Peru": 0.04,
        "Colombia": 0.03,
    },
}

# Bloomberg COUNTRY_OF_RISK two-letter -> T2 country name
BBG_TO_T2_COUNTRY = {
    "AU": "Australia", "CA": "Canada", "DK": "Denmark", "FR": "France",
    "DE": "Germany", "HK": "Hong Kong", "IT": "Italy", "JP": "Japan",
    "NL": "Netherlands", "SG": "Singapore", "ES": "Spain", "SE": "Sweden",
    "CH": "Switzerland", "GB": "U.K.", "US": "U.S.",
    "BR": "Brazil", "CL": "Chile",
    # CN is ambiguous - resolved via exchange code in resolve_china_split()
    "IN": "India", "ID": "Indonesia", "KR": "Korea", "MY": "Malaysia",
    "MX": "Mexico", "PH": "Philippines", "PL": "Poland",
    "SA": "Saudi Arabia", "ZA": "South Africa", "TW": "Taiwan",
    "TH": "Thailand", "TR": "Turkey", "VN": "Vietnam",
}

CHINA_A_EXCHANGES = {"CS", "CG", "C1", "C2"}  # Shanghai, Shenzhen
CHINA_H_EXCHANGES = {"HK"}                    # HKEX


# ============================================================================
# DATA LOADING
# ============================================================================

def load_etf_master(path: str = "etf_master_list.csv") -> pd.DataFrame:
    """Load the curated ETF master list with tier classifications."""
    df = pd.read_csv(path)
    df["tier"] = df["tier"].astype(int)
    df["currency_hedged"] = df["currency_hedged"].fillna("N").str.upper().eq("Y")
    return df


def get_bloomberg_session():
    """
    Get Bloomberg session using OpusBloomberg BBG class.
    
    Returns:
        BBG instance or None
    """
    if not BLOOMBERG_AVAILABLE:
        return None
    
    try:
        debug("Creating BBG session")
        return BBG()
    except Exception as e:
        debug(f"Failed to create BBG session: {e}")
        return None


def pull_etf_timeseries(tickers: list, start: str, end: Optional[str] = None) -> pd.DataFrame:
    """
    Pull daily shares outstanding, NAV, and AUM for each ETF.
    Returns long DataFrame: [date, ticker, shares_out, nav, aum]
    """
    bbg = get_bloomberg_session()
    if not bbg:
        print("Warning: No Bloomberg session available. Returning empty DataFrame.")
        return pd.DataFrame(columns=["date", "ticker", BBG_SHARES_OUT, BBG_NAV, BBG_AUM])
    
    end = end or datetime.today().strftime("%Y-%m-%d")
    bbg_tickers = [f"{t} US Equity" for t in tickers]
    fields = [BBG_SHARES_OUT, BBG_NAV, BBG_AUM]
    
    try:
        debug(f"Pulling historical data for {len(bbg_tickers)} tickers...")
        
        all_data = []
        
        with bbg:
            for ticker in bbg_tickers:
                start_date = start.replace("-", "")
                end_date = end.replace("-", "")
                
                hist_data = bbg.hist(ticker, fields, start_date, end_date)
                
                for point in hist_data:
                    all_data.append({
                        "date": point.get("date"),
                        "bbg_ticker": ticker,
                        BBG_SHARES_OUT: point.get(BBG_SHARES_OUT),
                        BBG_NAV: point.get(BBG_NAV),
                        BBG_AUM: point.get(BBG_AUM)
                    })
        
        df = pd.DataFrame(all_data)
        if df.empty:
            return df
        
        df["date"] = pd.to_datetime(df["date"])
        df["ticker"] = df["bbg_ticker"].str.replace(" US Equity", "", regex=False)
        return df.drop(columns=["bbg_ticker"])[["date", "ticker"] + fields]
        
    except Exception as e:
        debug(f"Error pulling historical data: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame(columns=["date", "ticker"] + fields)


def pull_etf_holdings(tickers: list, as_of: str) -> pd.DataFrame:
    """
    Pull holdings snapshot for each ETF as of a given date.
    Returns: [as_of, ticker, holding_ticker, holding_name, weight]
    
    NOTE: Bloomberg holdings reporting lags - use month-end T-5 for safety.
    Some issuers (iShares) update daily; others monthly.
    """
    bbg = get_bloomberg_session()
    if not bbg:
        print("Warning: No Bloomberg session available. Returning empty DataFrame.")
        return pd.DataFrame(columns=["as_of", "ticker", "holding_ticker",
                                     "holding_name", "weight"])
    
    bbg_tickers = [f"{t} US Equity" for t in tickers]
    
    try:
        debug(f"Pulling holdings for {len(bbg_tickers)} tickers as of {as_of}...")
        
        all_data = []
        
        with bbg:
            for ticker in bbg_tickers:
                # Use BDS with REFERENCE_DATE override
                overrides = {"REFERENCE_DATE": as_of.replace("-", "")}
                holdings_data = bbg.bds(ticker, BBG_HOLDINGS, overrides=overrides)
                
                for row in holdings_data:
                    row_data = {
                        "as_of": as_of,
                        "bbg_ticker": ticker,
                    }
                    # Copy all fields from the row
                    for key, value in row.items():
                        row_data[key] = value
                    all_data.append(row_data)
        
        if not all_data:
            return pd.DataFrame(columns=["as_of", "ticker", "holding_ticker",
                                         "holding_name", "weight"])
        
        df = pd.DataFrame(all_data)
        df["ticker"] = df["bbg_ticker"].str.replace(" US Equity", "", regex=False)
        df["as_of"] = pd.to_datetime(as_of)
        
        # Standardize column names
        rename_map = {c: c.lower().replace(" ", "_").replace("%_", "")
                      for c in df.columns}
        df = df.rename(columns=rename_map)
        
        return df
        
    except Exception as e:
        debug(f"Error pulling holdings: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame(columns=["as_of", "ticker", "holding_ticker",
                                     "holding_name", "weight"])


def map_holdings_to_country(holdings: pd.DataFrame) -> pd.DataFrame:
    """
    Map each underlying holding to its T2 country.
    Uses Bloomberg COUNTRY_OF_RISK with COUNTRY_OF_INCORPORATION fallback.
    Resolves China A vs H via exchange code.
    """
    if holdings.empty:
        return holdings
    
    bbg = get_bloomberg_session()
    if not bbg:
        print("Warning: No Bloomberg session available. Returning holdings without country mapping.")
        holdings["t2_country"] = None
        return holdings

    unique_holdings = holdings["holding_ticker"].dropna().unique().tolist()
    # Bloomberg expects fully-qualified tickers - assume holdings come as
    # "VALE US Equity" or similar; if just symbol, append "Equity"
    bbg_holdings = [h if " " in h else f"{h} Equity" for h in unique_holdings]

    try:
        debug(f"Mapping {len(bbg_holdings)} holdings to countries...")
        
        fields = ["COUNTRY_OF_RISK", "COUNTRY_OF_INCORPORATION", "EXCH_CODE"]
        
        with bbg:
            ref_data = bbg.ref_batch(bbg_holdings, fields)
        
        meta_data = []
        for security, data in ref_data.items():
            row_data = {
                "holding_full": security,
                "COUNTRY_OF_RISK": data.get("COUNTRY_OF_RISK"),
                "COUNTRY_OF_INCORPORATION": data.get("COUNTRY_OF_INCORPORATION"),
                "EXCH_CODE": data.get("EXCH_CODE")
            }
            meta_data.append(row_data)
        
        meta = pd.DataFrame(meta_data)
        meta["holding_ticker"] = meta["holding_full"].str.split(" ").str[0]
        meta["country_2c"] = meta["COUNTRY_OF_RISK"].fillna(
            meta["COUNTRY_OF_INCORPORATION"]
        )
        meta["t2_country"] = meta.apply(_resolve_country, axis=1)

        return holdings.merge(
            meta[["holding_ticker", "t2_country"]],
            on="holding_ticker",
            how="left",
        )
        
    except Exception as e:
        debug(f"Error mapping holdings to country: {e}")
        import traceback
        traceback.print_exc()
        holdings["t2_country"] = None
        return holdings


def _resolve_country(row) -> Optional[str]:
    """Apply BBG -> T2 mapping with China A/H exchange-code logic."""
    cc = row.get("country_2c")
    if pd.isna(cc):
        return None
    if cc == "CN":
        exch = str(row.get("EXCH_CODE", "")).upper()
        if exch in CHINA_A_EXCHANGES:
            return "ChinaA"
        return "ChinaH"  # default CN -> H (HKEX listings)
    return BBG_TO_T2_COUNTRY.get(cc)


# ============================================================================
# FLOW COMPUTATION (THE CORE FORMULA)
# ============================================================================

def compute_monthly_flows(etf_ts: pd.DataFrame) -> pd.DataFrame:
    """
    Net creation flow per ETF per month.

    Method: monthly_flow = (shares_out[end] - shares_out[start]) * mean_NAV
    
    This isolates true creation/redemption activity from market-driven AUM
    change. Shares outstanding only changes via creations or redemptions for
    an ETF, so delta-shares * NAV = net new capital.
    """
    df = etf_ts.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["ticker", "date"])
    df["month"] = df["date"].dt.to_period("M")

    monthly = df.groupby(["ticker", "month"]).agg(
        shares_start=(BBG_SHARES_OUT, "first"),
        shares_end=(BBG_SHARES_OUT, "last"),
        avg_nav=(BBG_NAV, "mean"),
        end_aum=(BBG_AUM, "last"),
    ).reset_index()

    monthly["delta_shares"] = monthly["shares_end"] - monthly["shares_start"]
    monthly["flow_usd"] = monthly["delta_shares"] * monthly["avg_nav"]
    monthly["date"] = monthly["month"].dt.to_timestamp(how="end").dt.normalize()

    return monthly[["date", "ticker", "flow_usd", "end_aum"]]


# ============================================================================
# COUNTRY ATTRIBUTION
# ============================================================================

def get_country_weights(
    ticker: str,
    region_tag: str,
    date: pd.Timestamp,
    holdings: pd.DataFrame,
) -> dict:
    """
    Country composition for a regional ETF as of a date.
    Prefers actual holdings; falls back to static REGIONAL_FALLBACK_WEIGHTS.
    """
    if not holdings.empty:
        h = holdings[(holdings["ticker"] == ticker) & (holdings["as_of"] <= date)]
        if not h.empty:
            latest = h[h["as_of"] == h["as_of"].max()]
            wts = latest.groupby("t2_country")["weight"].sum()
            wts = wts[wts.index.notna() & (wts > 0)]
            if len(wts) > 0:
                return (wts / wts.sum()).to_dict()
    return REGIONAL_FALLBACK_WEIGHTS.get(region_tag, {})


def attribute_flows_to_countries(
    flows: pd.DataFrame,
    holdings: pd.DataFrame,
    master: pd.DataFrame,
) -> pd.DataFrame:
    """
    Allocate each ETF's monthly flow to T2 countries.
    Single-country ETF: 100% to primary_country.
    Regional ETF: split by month-end country weights.
    Returns: [date, ticker, country, tier, country_flow, country_aum]
    """
    flows = flows.merge(
        master[["ticker", "primary_country", "tier"]],
        on="ticker",
        how="left",
    )

    is_regional = flows["primary_country"].str.startswith("REGIONAL_", na=False)

    # Single-country: trivial attribution
    single = flows[~is_regional].copy()
    single["country"] = single["primary_country"]
    single["country_flow"] = single["flow_usd"]
    single["country_aum"] = single["end_aum"]

    # Regional: split by weights
    regional_rows = []
    for _, row in flows[is_regional].iterrows():
        weights = get_country_weights(
            row["ticker"], row["primary_country"], row["date"], holdings,
        )
        for country, w in weights.items():
            if country in T2_COUNTRIES:
                regional_rows.append({
                    "date": row["date"],
                    "ticker": row["ticker"],
                    "country": country,
                    "tier": row["tier"],
                    "country_flow": row["flow_usd"] * w,
                    "country_aum": row["end_aum"] * w,
                })
    regional = pd.DataFrame(regional_rows)

    cols = ["date", "ticker", "country", "tier", "country_flow", "country_aum"]
    return pd.concat(
        [single[cols], regional[cols] if not regional.empty else pd.DataFrame(columns=cols)],
        ignore_index=True,
    )


# ============================================================================
# TIER AGGREGATION
# ============================================================================

def aggregate_to_country_tier(attributed: pd.DataFrame) -> pd.DataFrame:
    """Roll up to (date, country, tier) panel."""
    return attributed.groupby(["date", "country", "tier"]).agg(
        flow=("country_flow", "sum"),
        aum=("country_aum", "sum"),
        n_etfs=("ticker", "nunique"),
    ).reset_index()


# ============================================================================
# T2 SIGNAL DERIVATION (THE OUTPUT THAT FEEDS NORMALIZED_T2)
# ============================================================================

def derive_t2_signals(panel: pd.DataFrame) -> pd.DataFrame:
    """
    Six monthly factors per country, ready for Step Two _CS / _TS normalization.
    """
    flow_w = panel.pivot_table(index=["date", "country"], columns="tier",
                                values="flow", aggfunc="sum", fill_value=0.0)
    flow_w.columns = [f"tier{int(c)}_flow" for c in flow_w.columns]

    aum_w = panel.pivot_table(index=["date", "country"], columns="tier",
                               values="aum", aggfunc="sum", fill_value=0.0)
    aum_w.columns = [f"tier{int(c)}_aum" for c in aum_w.columns]

    df = flow_w.join(aum_w).reset_index()

    for k in range(1, 6):
        if f"tier{k}_flow" not in df.columns:
            df[f"tier{k}_flow"] = 0.0
        if f"tier{k}_aum" not in df.columns:
            df[f"tier{k}_aum"] = 0.0

    flow_cols = [f"tier{k}_flow" for k in range(1, 6)]
    aum_cols  = [f"tier{k}_aum"  for k in range(1, 6)]
    df["total_flow"] = df[flow_cols].sum(axis=1)
    df["total_aum"]  = df[aum_cols].sum(axis=1)

    # Lagged AUM for normalization (use prior month-end)
    df = df.sort_values(["country", "date"])
    df["total_aum_lag"] = df.groupby("country")["total_aum"].shift(1)

    # SIGNAL 1: Total flow as % of lagged AUM
    df["ETF_Total_Flow_pct_AUM"] = df["total_flow"] / df["total_aum_lag"]

    # SIGNAL 2: Sticky share = tier 1 / |total flow|
    # Use absolute total to handle reversal months meaningfully
    df["ETF_Sticky_Share"] = (
        df["tier1_flow"] / df["total_flow"].abs().replace(0, np.nan)
    )

    # SIGNAL 3: Smart-Sticky Divergence (the flagship)
    # (smart_beta + active) - passive, scaled by AUM
    smart_minus_sticky = (df["tier2_flow"] + df["tier3_flow"]) - df["tier1_flow"]
    df["ETF_Smart_Sticky_Divergence"] = smart_minus_sticky / df["total_aum_lag"]

    # SIGNAL 4: Forced-Seller Indicator (only when tier 1 outflow)
    df["ETF_Forced_Seller_Indicator"] = np.where(
        df["tier1_flow"] < 0,
        df["tier1_flow"] / df["total_aum_lag"],
        0.0,
    )

    # SIGNAL 5: Thematic Crowding = tier 4 / |total|
    df["ETF_Thematic_Crowding"] = (
        df["tier4_flow"] / df["total_flow"].abs().replace(0, np.nan)
    )

    # SIGNAL 6: Levered Net Positioning
    # Tier 5 AUM only - sign needs to be applied by ETF naming convention
    # (ending in 'bear/short/inverse' vs 'bull/long')
    # In production, split tier5 in master CSV: leveraged_3x_long vs _short
    # Then aggregate as: (long_aum - short_aum) / total_aum_lag
    df["ETF_Levered_Net_Positioning"] = df["tier5_aum"] / df["total_aum_lag"]

    # Coverage gates
    insufficient = df["total_aum_lag"] < MIN_COUNTRY_TOTAL_AUM
    flow_signals = ["ETF_Total_Flow_pct_AUM", "ETF_Smart_Sticky_Divergence",
                    "ETF_Forced_Seller_Indicator", "ETF_Levered_Net_Positioning"]
    df.loc[insufficient, flow_signals] = np.nan

    insufficient_tier1 = df["tier1_aum"] < MIN_TIER_AUM_USD
    df.loc[insufficient_tier1, ["ETF_Sticky_Share", "ETF_Forced_Seller_Indicator"]] = np.nan

    return df[[
        "date", "country",
        "ETF_Total_Flow_pct_AUM",
        "ETF_Sticky_Share",
        "ETF_Smart_Sticky_Divergence",
        "ETF_Forced_Seller_Indicator",
        "ETF_Thematic_Crowding",
        "ETF_Levered_Net_Positioning",
    ]]


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    # 1. Load master list
    master = load_etf_master("etf_master_list.csv")
    print(f"Loaded {len(master)} ETFs across "
          f"{master['primary_country'].nunique()} country buckets")

    # 2. Pull daily time series
    print("Pulling Bloomberg time series...")
    ts = pull_etf_timeseries(master["ticker"].tolist(), START_DATE, END_DATE)
    ts.to_parquet(OUTPUT_DIR / "etf_timeseries.parquet")

    # 3. Pull monthly holdings snapshots for regional ETFs
    print("Pulling holdings snapshots...")
    regional_etfs = master[master["primary_country"].str.startswith("REGIONAL_")]
    end = pd.Timestamp(END_DATE) if END_DATE else pd.Timestamp.today()
    month_ends = pd.date_range(START_DATE, end, freq="ME")

    holdings_panels = []
    for me in month_ends:
        try:
            h = pull_etf_holdings(
                regional_etfs["ticker"].tolist(),
                as_of=me.strftime("%Y-%m-%d"),
            )
            if not h.empty:
                holdings_panels.append(h)
        except Exception as e:
            print(f"Holdings pull failed for {me}: {e}")
            continue

    if holdings_panels:
        holdings = pd.concat(holdings_panels, ignore_index=True)
        holdings = map_holdings_to_country(holdings)
        holdings.to_parquet(OUTPUT_DIR / "etf_holdings.parquet")
    else:
        print("WARNING: no holdings retrieved - falling back to static weights")
        holdings = pd.DataFrame()

    # 4. Compute monthly flows per ETF
    flows = compute_monthly_flows(ts)
    flows.to_parquet(OUTPUT_DIR / "etf_flows_raw.parquet")

    # 5. Attribute to countries
    attributed = attribute_flows_to_countries(flows, holdings, master)

    # 6. Aggregate by tier
    panel = aggregate_to_country_tier(attributed)
    panel.to_parquet(OUTPUT_DIR / "etf_country_tier_panel.parquet")

    # 7. Derive T2 signals
    signals = derive_t2_signals(panel)
    signals.to_csv(OUTPUT_DIR / "etf_signals_t2.csv", index=False)

    print(f"\nDone. Wrote {len(signals)} signal rows for "
          f"{signals['country'].nunique()} countries.")
    print(f"Date range: {signals['date'].min()} to {signals['date'].max()}")
    print(f"Output: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    # Set up Bloomberg connection before running main
    if BLOOMBERG_AVAILABLE:
        try:
            print("Setting up Bloomberg connection...")
            bloomberg_setup(verbose=True)
            print("Bloomberg connection ready.")
        except Exception as e:
            print(f"Warning: Bloomberg setup failed: {e}")
            print("Continuing without Bloomberg data (will return empty DataFrames)...")
    
    try:
        main()
    except Exception as e:
        print(f"Error in main: {e}")
        import traceback
        traceback.print_exc()

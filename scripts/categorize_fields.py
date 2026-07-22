"""
=============================================================================
SCRIPT NAME: categorize_fields.py
=============================================================================

INPUT FILES:
- Production Data/Bloomberg Master Field List.xlsx: Bloomberg field catalog

OUTPUT FILES:
- /tmp/field_categories.txt: categorized breakdown

VERSION: 1.0
LAST UPDATED: 2026-04-27

DESCRIPTION:
Categorizes all 3,144 Bloomberg fields into domains to see what we already
cover and what's missing for equities, ETFs, and indices.

DEPENDENCIES:
- pandas, openpyxl

USAGE:
python scripts/categorize_fields.py
=============================================================================
"""

import pandas as pd
from pathlib import Path
from collections import defaultdict

CATALOG_PATH = Path(__file__).resolve().parent.parent / "Production Data" / "Bloomberg Master Field List.xlsx"

# Keyword-based domain classification rules
DOMAIN_RULES = {
    "Price & Volume": [
        "PX_", "PRICE", "HIGH", "LOW", "OPEN", "CLOSE", "VOLUME", "TURNOVER",
        "VWAP", "TRADE", "BID", "ASK", "SPREAD", "LAST", "CHANGE", "RETURN",
        "ADVANC", "DECLINE", "TICK", "TRDVOL", "AVRG", "AVERAGE"
    ],
    "Valuation": [
        "PE_", "P/E", "PB_", "P/B", "PS_", "P/S", "PCF", "EV/", "EV_",
        "PRICE_TO_BOOK", "PRICE_TO_EARN", "PRICE_TO_SALE", "PRICE_TO_CASH",
        "DIV_YIELD", "DVD_YIELD", "DIVIDEND", "YIELD", "TOTAL_RETURN",
        "ENTERPRISE_VALUE", "MARKET_CAP", "MKT_CAP", "CUR_MKT_CAP",
        "EARNINGS_YIELD", "FCF_YIELD", "CAPE"
    ],
    "Growth": [
        "GROWTH", "GROW", "MOMENTUM", "EPS_GROW", "SALES_GROWTH",
        "PROFIT_GROWTH", "EBITDA_GROWTH", "REVENUE_GROWTH",
        "DIVIDEND_GROWTH", "DRIV"
    ],
    "Profitability": [
        "PROFIT_MARGIN", "ROS", "ROE", "ROA", "ROCE", "ROIC",
        "RETURN_ON_", "RETURN_ON_CAP", "RETURN_COM_EQY", "ROA",
        "MARGIN", "OP_MARGIN", "NET_MARGIN", "GROSS_MARGIN",
        "EBITDA", "EBIT", "NET_INCOME", "NOPAT", "NI_"
    ],
    "Financial Health": [
        "DEBT", "LEVERAGE", "COVERAGE", "LIQUIDITY", "QUICK_RATIO",
        "CURRENT_RATIO", "SOLVENCY", "INTEREST_COVER", "DIVIDEND_COVER",
        "CASH_RATIO", "NET_DEBT", "TOTAL_DEBT", "LTD_DEBT",
        "DEBT_TO_EQUITY", "DEBT_TO_ASSET", "DEBT_TO_EBITDA",
        "NET_DEBT_TO_EBITDA", "FIXED_CHARGE_COVER"
    ],
    "Cash Flow": [
        "CASH_FLOW", "FCF", "FREE_CASH", "OPERATING_CF", "FINANCING_CF",
        "INVESTING_CF", "CAPEX", "CASH_FROM_OPS", "CASH_AND_MARKETABLE",
        "CASH_AND_INVEST", "CASH_AND_EQUIV", "CF_", "NET_CASH"
    ],
    "Efficiency": [
        "ASSET_TURNOVER", "INVENTORY_TURN", "RECEIVABLES_TURN",
        "PAYABLES_TURN", "DAYS_INVENTORY", "DAYS_SALES_OUT",
        "DAYS_PAYABLE", "DAYS_RECEIVABLE", "EFFICIENCY",
        "CAPEX_TO_SALES", "CAPEX_TO_DEPRECIATION"
    ],
    "Estimates & Consensus": [
        "BEST_", "ESTIMATE", "CONSENSUS", "TARGET_PRICE", "RECOMMEND",
        "SELLSIDE", "NUM_EST", "STD_EST", "HIGH_EST", "LOW_EST",
        "MEAN_EST", "MEDIAN_EST", "CURRENT_EST", "NEXT_EST",
        "TARGET_MEAN", "TARGET_MEDIAN", "TARGET_HIGH", "TARGET_LOW",
        "TOTAL_RECOMMEND", "BUY_RATIO", "SELL_RATIO", "HOLD_RATIO"
    ],
    "ESG & Sustainability": [
        "ESG", "ENVIRONMENT", "SOCIAL", "GOVERNANCE", "SUSTAINABIL",
        "CARBON", "EMISSION", "DIVERSITY", "BOARD_", "INDEPENDENT_DIR",
        "GREEN_", "CLIMATE", "WASTE", "WATER"
    ],
    "Risk": [
        "VOLATILITY", "VOLATIL", "BETA", "ALPHA", "SHARPE", "TREYNOR",
        "SORTINO", "STD_DEV", "STANDARD_DEV", "VARIANCE", "COVARIANCE",
        "CORRELATION", "RSQUARED", "R_SQUARED", "TRACKING_ERROR",
        "DRAWDOWN", "MAX_DRAWDOWN", "SKEWNESS", "KURTOSIS", "VAR_",
        "CVAR", "EXPECTED_SHORTFALL", "TAIL_RISK", "DOWNSIDE",
        "UPSIDE", "CAPM", "RISK_FREE", "RISK_PREMIUM"
    ],
    "Technical Analysis": [
        "MOV_AVG", "MOVING_AVERAGE", "SMA_", "EMA_", "MACD", "RSI",
        "STOCHASTIC", "BOLLINGER", "BOLU", "BOLD", "AVG_TRUE_RANGE",
        "ATR", "ADX", "DMI", "MFI", "MONEY_FLOW", "OBV", "ON_BALANCE",
        "RELATIVE_STRENGTH", "WILLIAMS_R", "WILLIAM_R", "CCI",
        "COMMODITY_CHANNEL", "CHAIKIN", "AROON", "ROC", "RATE_OF_CHANGE",
        "ULTIMATE_OSCILLATOR", "FIBONACCI", "SUPPORT", "RESISTANCE",
        "ICHIMOKU", "PARABOLIC_SAR", "SAR_", "PVT"
    ],
    "ETF-Specific": [
        "PREMIUM", "DISCOUNT", "NAV", "NET_ASSET_VALUE", "EXPENSE_RATIO",
        "HOLDINGS", "TOP_HOLDINGS", "SECTOR_WEIGHT", " INDUSTRY_WEIGHT",
        "TRACKING_DIFF", "CREATION", "REDEMPTION", "AUTHORIZED_PARTICIP",
        "IN_KIND", "DIVIDEND_SCHEDULE", "ETP_"
    ],
    "Index-Specific": [
        "INDEX_MEMBER", "INDEX_WEIGHT", "INDEX_FACTOR", "SECTOR_ALLOC",
        "INDEX_DIV_POINT", "INDEX_DIV_YIELD", "INDEX_PRICE_EARN",
        "INDEX_PRICE_BOOK", "INDEX_MARKET_CAP", "FREE_FLOAT",
        "WEIGHT_IN_INDEX", "MEMBERSHIP", "CONSTITUENT", "INDEX_"
    ],
    "Fundamental - Income Statement": [
        "SALES", "REVENUE", "INCOME", "EARNINGS", "EPS_", "EPS_ACTUAL",
        "NET_INCOME", "OPERATING_INCOME", "PRETAX_INCOME", "NORMALIZED_EARN",
        "DILUTED_EPS", "BASIC_EPS", "ADJUSTED_EPS", "GROSS_PROFIT",
        "SALES_REV_TURN", "OPER_REV", "NONOPER_INCOME"
    ],
    "Fundamental - Balance Sheet": [
        "TOTAL_ASSETS", "TOTAL_LIABILITIES", "SHAREHOLDER_EQUITY",
        "BOOK_VALUE", "BOOK_VAL", "TANGIBLE_BOOK", "TOTAL_CAPITAL",
        "WORKING_CAPITAL", "CURRENT_ASSETS", "NONCURRENT_ASSETS",
        "INTANGIBLE_ASSETS", "GOODWILL", "PPE", "PROPERTY_PLANT",
        "INVENTORY", "RECEIVABLES", "PAYABLES", "ACCRUED_",
        "DEFERRED_", "RETAINED_EARNINGS", "COMMON_EQUITY",
        "TREASURY_STOCK", "PREFERRED_STOCK", "MINORITY_INTEREST"
    ],
    "Fundamental - Per Share": [
        "PER_SHARE", "BOOK_VAL_PER_SH", "TANGIBLE_BV_PER_SH", "CASH_PER_SHARE",
        "REVENUE_PER_SHARE", "FCF_PER_SHARE", "DIVIDENDS_PER_SHARE",
        "DPS", "SPS", "CFPS", "BVPS", "TBVPS"
    ],
    "Ownership & Liquidity": [
        "SHORT_INTEREST", "SHORT_RATIO", "SHORT_OUTSTANDING",
        "DAYS_TO_COVER", "FLOAT", "SHARES_OUTSTANDING", "AVERAGE_VOLUME",
        "INSIDER_OWNERSHIP", "INSTITUTIONAL_OWNERSHIP", "MAJOR_HOLDER",
        "CONCENTRATION", "HHI", "BORROW_FEE", "UTILIZATION",
        "ON_LOAN", "LENDABLE"
    ],
    "Corporate Actions": [
        "SPLIT", "DIVIDEND", "BUYBACK", "REPURCHASE", "STOCK_SPLIT",
        "REVERSE_SPLIT", "RIGHTS_ISSUE", "SPINOFF", "MERGER",
        "ACQUISITION", "TENDER_OFFER", "DELISTING", "LISTING"
    ],
    "Derivatives & Options": [
        "OPTION", "FUTURE", "IMPLIED_VOLATILITY", "IV_", "DELTA", "GAMMA",
        "VEGA", "THETA", "RHO", "OPEN_INTEREST", "OPTION_VOLUME",
        "PUT_CALL_RATIO", "PCR", "GREEKS"
    ],
    "Macro & Economic": [
        "CPI", "GDP", "INFLATION", "UNEMPLOYMENT", "INTEREST_RATE",
        "FED_FUNDS", "TREASURY", "BENCHMARK", "SPREAD_",
        "YIELD_CURVE", "SWAP_", "ZERO_COUPON", "OIS_", "LIBOR",
        "EURIBOR", "SOFR", "SONIA", "ESTR"
    ],
    "FX": [
        "FX_", "FOREX", "CURRENCY", "SPOT", "FORWARD_",
        "CROSS_RATE", "PPP_", "REER", "NEER", "FX_VOLATILITY",
        "FX_IMPLIED"
    ],
    "Commodity": [
        "COMMODITY", "COMDTY", "COMMOD", "GOLD", "SILVER", "OIL",
        "NATURAL_GAS", "COPPER", "ALUMINUM", "WHEAT", "CORN",
        "SOYBEAN", "LME_"
    ],
    "Fixed Income": [
        "BOND", "YIELD_", "YAS_", "DURATION", "CONVEXITY", "COUPON",
        "MATURITY", "MTG", "SPREAD_TO", "OAS", "Z_SPREAD", "G_SPREAD",
        "I_SPREAD", "CALLABLE", "PUTABLE", "SINKABLE", "RATING",
        "CREDIT_RATING", "MOODY", "S&P_", "FITCH", "RECOVERY_RATE",
        "LOSS_GIVEN_DEFAULT", "PROBABILITY_OF_DEFAULT"
    ],
    "Analyst & Rating": [
        "RATING", "RECOMMENDATION", "UPGRADE", "DOWNGRADE",
        "PRICE_TARGET", "PT_", "ANALYST_COVERAGE"
    ],
    "Descriptive & Reference": [
        "NAME", "TICKER", "SEDOL", "CUSIP", "ISIN", "FIGI", "BLOOMBERG_ID",
        "INDUSTRY", "SECTOR", "CLASSIFICATION", "GICS", "BICS",
        "COUNTRY", "EXCHANGE", "CURRENCY", "DESCRIPTION",
        "SECURITY_TYPE", "SECURITY_TYP", "ISSUER", "MARKET_STATUS",
        "TRADING_HOURS", "LOT_SIZE", "PAR_VALUE", "FACE_VALUE"
    ],
    "Calendar & Seasonality": [
        "EARNINGS_DATE", "EX_DIV_DATE", "PAYABLE_DATE", "RECORD_DATE",
        "ANNUAL_REPORT_DATE", "FISCAL_YEAR", "FISCAL_QUARTER",
        "MONTHLY", "QUARTERLY", "ANNUAL", "SEASONAL", "CYCLE"
    ],
    "Real Estate (REIT)": [
        "FFO", "FUNDS_FROM_OPS", "AFFO", "ADJUSTED_FFO", "NAV_",
        "REIT_", "NOI", "NET_OPERATING_INCOME", "CAP_RATE",
        "OCCUPANCY", "RENT_", "SAME_STORE"
    ],
}

def main():
    df = pd.read_excel(CATALOG_PATH, sheet_name="Pruned List")
    
    # Get field mnemonics from Column B
    fields = df.iloc[:, 1].dropna().tolist()
    fields = [str(f).strip() for f in fields if str(f).strip()]
    
    # Categorize each field
    categories = defaultdict(list)
    uncategorized = []
    
    for field in fields:
        field_upper = field.upper()
        assigned = False
        for category, keywords in DOMAIN_RULES.items():
            for kw in keywords:
                if kw in field_upper:
                    categories[category].append(field)
                    assigned = True
                    break
            if assigned:
                break
        if not assigned:
            uncategorized.append(field)
    
    print(f"\n{'='*70}")
    print(f"FIELD CATEGORIZATION REPORT")
    print(f"{'='*70}")
    print(f"Total fields analyzed: {len(fields)}")
    
    total_categorized = 0
    for category in sorted(categories.keys()):
        count = len(categories[category])
        total_categorized += count
        print(f"\n{'─'*70}")
        print(f"{category}: {count} fields")
        print(f"{'─'*70}")
        for f in sorted(categories[category]):
            print(f"  {f}")
    
    print(f"\n{'='*70}")
    print(f"UNCATEGORIZED FIELDS: {len(uncategorized)}")
    print(f"{'='*70}")
    for f in sorted(uncategorized):
        print(f"  {f}")
    
    # Summary stats
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"Total: {len(fields)}")
    print(f"Categorized: {total_categorized}")
    print(f"Uncategorized: {len(uncategorized)}")
    
    # Identify domain gaps
    print(f"\n{'='*70}")
    print(f"CANDIDATE GAPS (areas where coverage is thin)")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()

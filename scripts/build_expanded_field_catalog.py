"""
=============================================================================
SCRIPT NAME: build_expanded_field_catalog.py
=============================================================================

INPUT FILES:
- Production Data/Bloomberg Master Field List.xlsx: Existing 3,674-field catalog

OUTPUT FILES:
- Production Data/Expanded_Field_Catalog.xlsx: Comprehensive field catalog with
  categories, status (existing vs new), and coverage analysis

VERSION: 1.0
LAST UPDATED: 2026-04-27

DESCRIPTION:
Creates an expanded Bloomberg field catalog by combining the existing master
field list with discovered fields from web research and Bloomberg documentation.
Each field is categorized by domain (Price, Valuation, Fundamentals, ESG,
Technical, ETF, Index, etc.) and flagged as "Existing" or "New Addition" so
you can see exactly what's being added.

DEPENDENCIES:
- pandas, openpyxl, xlsxwriter

USAGE:
conda run -p "/Users/arjundivecha/Dropbox/AAA Backup/A Working/OpusBloomberg/.venv" python scripts/build_expanded_field_catalog.py

NOTES:
- New fields are sourced from Bloomberg API documentation, community references,
  and known Bloomberg terminal mnemonics (//blp/refdata service)
- Not all new fields may work for all security types — testing is recommended
- Fields are marked with categories for easy browsing
=============================================================================
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
CATALOG_PATH = BASE_DIR / "Production Data" / "Bloomberg Master Field List.xlsx"
OUTPUT_PATH = BASE_DIR / "Production Data" / "Expanded_Field_Catalog.xlsx"
SHEET_NAME = "Pruned List"

# ────────────────────────────────────────────────────────────────────
# COMPREHENSIVE FIELD CATALOG
# Organized by domain. Each entry: (mnemonic, description, category, sub_category)
# Fields marked as EXISTING are confirmed in the master list.
# NEW entries are sourced from web research + known Bloomberg fields.
# ────────────────────────────────────────────────────────────────────

NEW_FIELDS = [
    # ===== TECHNICAL ANALYSIS (most of these are missing) =====
    ("PX_AVERAGE_20D", "20-day average price", "Technical", "Moving Averages"),
    ("PX_AVERAGE_50D", "50-day average price", "Technical", "Moving Averages"),
    ("PX_AVERAGE_200D", "200-day average price", "Technical", "Moving Averages"),
    ("RSI_INDEX_14D", "14-day Relative Strength Index", "Technical", "RSI / Momentum"),
    ("MACD", "Moving Average Convergence Divergence line", "Technical", "MACD"),
    ("MACD_SIGNAL", "MACD signal line (9-day EMA of MACD)", "Technical", "MACD"),
    ("MACD_HISTOGRAM", "MACD histogram (MACD - Signal)", "Technical", "MACD"),
    ("BOLLINGER_UPPER", "Upper Bollinger Band (20d SMA + 2σ)", "Technical", "Bollinger Bands"),
    ("BOLLINGER_LOWER", "Lower Bollinger Band (20d SMA - 2σ)", "Technical", "Bollinger Bands"),
    ("BOLLINGER_MIDDLE", "Middle Bollinger Band (20d SMA)", "Technical", "Bollinger Bands"),
    ("STOCHASTIC_14D", "14-day stochastic oscillator %K", "Technical", "Stochastic"),
    ("AVG_TRUE_RANGE_14D", "14-day average true range (ATR)", "Technical", "Volatility"),
    ("ADX_14D", "14-day Average Directional Index", "Technical", "ADX / DMI"),
    ("DI_PLUS_14D", "14-day Plus Directional Indicator (+DI)", "Technical", "ADX / DMI"),
    ("DI_MINUS_14D", "14-day Minus Directional Indicator (-DI)", "Technical", "ADX / DMI"),
    ("CCI_20D", "20-day Commodity Channel Index", "Technical", "Momentum"),
    ("MFI_14D", "14-day Money Flow Index", "Technical", "Volume"),
    ("OBV", "On-Balance Volume", "Technical", "Volume"),
    ("WILLIAMS_R_14D", "14-day Williams %R oscillator", "Technical", "Momentum"),
    ("CHAIKIN_OSCILLATOR", "Chaikin Oscillator", "Technical", "Volume"),
    ("AROON_UP_14D", "14-day Aroon Up indicator", "Technical", "Momentum"),
    ("AROON_DOWN_14D", "14-day Aroon Down indicator", "Technical", "Momentum"),
    ("SMAX_50D", "Current price distance from 50-day SMA (%)", "Technical", "Moving Averages"),
    ("SMAX_200D", "Current price distance from 200-day SMA (%)", "Technical", "Moving Averages"),
    ("VOLATILITY_30D", "30-day historical volatility (annualized)", "Technical", "Volatility"),
    ("VOLATILITY_60D", "60-day historical volatility (annualized)", "Technical", "Volatility"),
    ("VOLATILITY_90D", "90-day historical volatility (annualized)", "Technical", "Volatility"),
    ("VOLATILITY_180D", "180-day historical volatility (annualized)", "Technical", "Volatility"),
    ("VOLATILITY_1YR", "1-year historical volatility (annualized)", "Technical", "Volatility"),
    ("TOTAL_RETURN_INDEX", "Total return index (price + dividends reinvested)", "Technical", "Returns"),
    ("TRAIL_1M_RETURN", "Trailing 1-month price return (%)", "Technical", "Returns"),
    ("TRAIL_3M_RETURN", "Trailing 3-month price return (%)", "Technical", "Returns"),
    ("TRAIL_6M_RETURN", "Trailing 6-month price return (%)", "Technical", "Returns"),
    ("TRAIL_12M_RETURN", "Trailing 12-month price return (%)", "Technical", "Returns"),
    ("TRAIL_1M_TOTAL_RETURN", "Trailing 1-month total return (%)", "Technical", "Returns"),
    ("TRAIL_3M_TOTAL_RETURN", "Trailing 3-month total return (%)", "Technical", "Returns"),
    ("TRAIL_6M_TOTAL_RETURN", "Trailing 6-month total return (%)", "Technical", "Returns"),
    ("TRAIL_12M_TOTAL_RETURN", "Trailing 12-month total return (%)", "Technical", "Returns"),

    # ===== RISK / FACTOR FIELDS (mostly missing) =====
    ("BETA_RAW", "Raw beta vs S&P 500 (2-year weekly)", "Risk", "Beta"),
    ("BETA_ADJUSTED", "Adjusted beta (Bloomberg adjusted)", "Risk", "Beta"),
    ("ALPHA_RAW", "Raw alpha (excess return vs benchmark)", "Risk", "Alpha"),
    ("RSQUARED", "R-squared from beta regression", "Risk", "Beta"),
    ("TREYNOR_RATIO", "Treynor ratio (excess return / beta)", "Risk", "Risk Ratios"),
    ("SORTINO_RATIO", "Sortino ratio (downside deviation)", "Risk", "Risk Ratios"),
    ("MAX_DRAWDOWN_12M", "Maximum drawdown over 12 months (%)", "Risk", "Drawdown"),
    ("SKEWNESS_1YR", "1-year return skewness", "Risk", "Distribution"),
    ("KURTOSIS_1YR", "1-year return kurtosis", "Risk", "Distribution"),
    ("VAR_95_1D", "Value at Risk 95% 1-day", "Risk", "VaR"),
    ("TAIL_RISK_95", "Tail risk measure (CVaR 95%)", "Risk", "VaR"),
    ("CORRELATION_SPX_1YR", "1-year correlation with S&P 500", "Risk", "Correlation"),

    # ===== VALUATION (some missing) =====
    ("FORWARD_PE_RATIO", "Forward price-to-earnings ratio", "Valuation", "PE-Based"),
    ("TRAIL_PE_RATIO", "Trailing price-to-earnings ratio", "Valuation", "PE-Based"),
    ("PX_TO_EBITDA", "Price-to-EBITDA ratio", "Valuation", "Multiples"),
    ("PX_TO_CASH_FLOW", "Price-to-cash flow ratio", "Valuation", "Multiples"),
    ("EV_TO_SALES", "Enterprise value / Revenue", "Valuation", "EV Multiples"),
    ("EV_TO_EBIT", "Enterprise value / EBIT", "Valuation", "EV Multiples"),
    ("EARNINGS_YIELD", "Earnings yield (EPS / Price, inverse of PE)", "Valuation", "Yield-Based"),
    ("FCF_YIELD", "Free cash flow yield (FCF / Market Cap)", "Valuation", "Yield-Based"),
    ("CAPE_RATIO", "Cyclically adjusted PE (Shiller PE)", "Valuation", "PE-Based"),
    ("EV_TO_INVESTED_CAPITAL", "Enterprise value / Invested capital", "Valuation", "EV Multiples"),
    ("SALES_YIELD", "Sales yield (Revenue / Market Cap)", "Valuation", "Yield-Based"),

    # ===== PROFITABILITY (some missing) =====
    ("RETURN_ON_INV_CAP", "Return on invested capital (ROIC)", "Profitability", "Returns"),
    ("FCF_MARGIN", "Free cash flow margin (FCF / Revenue)", "Profitability", "Margins"),
    ("EBITDA_MARGIN", "EBITDA margin", "Profitability", "Margins"),
    ("EBIT_MARGIN", "EBIT margin", "Profitability", "Margins"),
    ("PRETAX_MARGIN", "Pre-tax profit margin", "Profitability", "Margins"),
    ("NOPAT", "Net operating profit after tax", "Profitability", "Absolute"),
    ("GROSS_PROFIT", "Gross profit", "Profitability", "Absolute"),

    # ===== GROWTH =====
    ("BEST_EPS_GROWTH", "Consensus EPS growth rate (next FY)", "Growth", "EPS Growth"),
    ("BEST_LT_EPS_GROWTH", "Consensus long-term EPS growth rate", "Growth", "EPS Growth"),
    ("BEST_SALES_GROWTH", "Consensus sales growth rate", "Growth", "Sales Growth"),
    ("SUSTAINABLE_GROWTH", "Sustainable growth rate (ROE × retention ratio)", "Growth", "Fundamental Growth"),
    ("5Y_SALES_GROWTH", "5-year compounded sales growth rate", "Growth", "Historical Growth"),
    ("5Y_EPS_GROWTH", "5-year compounded EPS growth rate", "Growth", "Historical Growth"),
    ("5Y_DVD_GROWTH", "5-year compounded dividend growth rate", "Growth", "Historical Growth"),
    ("REINVESTMENT_RATE", "Reinvestment rate (1 - payout ratio)", "Growth", "Fundamental Growth"),

    # ===== ESTIMATES / CONSENSUS (several missing) =====
    ("BEST_TARGET_PRICE_HIGH", "Highest analyst target price", "Estimates", "Target Price"),
    ("BEST_TARGET_PRICE_LOW", "Lowest analyst target price", "Estimates", "Target Price"),
    ("NUM_ESTIMATES", "Number of analyst estimates for EPS", "Estimates", "Coverage"),
    ("NUM_UPGRADES", "Number of analyst upgrades (last 1M)", "Estimates", "Revisions"),
    ("NUM_DOWNGRADES", "Number of analyst downgrades (last 1M)", "Estimates", "Revisions"),
    ("EPS_REVISION_RATIO", "EPS revision ratio (ups/downs)", "Estimates", "Revisions"),
    ("SALES_REVISION_RATIO", "Sales revision ratio (ups/downs)", "Estimates", "Revisions"),
    ("EARNINGS_SURPRISE", "Earnings surprise (actual - consensus)", "Estimates", "Surprises"),
    ("EARNINGS_SURPRISE_PCT", "Earnings surprise percentage", "Estimates", "Surprises"),
    ("FORWARD_12M_EPS", "Forward 12-month EPS (derived)", "Estimates", "EPS"),
    ("FORWARD_12M_SALES", "Forward 12-month sales", "Estimates", "Revenue"),
    ("BEST_EBITDA", "Consensus EBITDA estimate", "Estimates", "Profitability"),
    ("BEST_NET_INCOME", "Consensus net income estimate", "Estimates", "Profitability"),
    ("BEST_DPS", "Consensus dividend per share estimate", "Estimates", "Dividends"),

    # ===== BALANCE SHEET (several BS_ prefix fields missing) =====
    ("BS_TOT_ASSET", "Total assets (balance sheet)", "Balance Sheet", "Assets"),
    ("BS_TOT_LIAB", "Total liabilities (balance sheet)", "Balance Sheet", "Liabilities"),
    ("BS_LT_BORROW", "Long-term borrowings", "Balance Sheet", "Liabilities"),
    ("BS_CASH_AND_MARKETABLE", "Cash and marketable securities", "Balance Sheet", "Assets"),
    ("BS_CASH", "Cash & cash equivalents", "Balance Sheet", "Assets"),
    ("BS_TOTAL_DEBT", "Total debt (short + long term)", "Balance Sheet", "Liabilities"),
    ("BS_PREFERRED_EQY", "Preferred equity", "Balance Sheet", "Equity"),
    ("BS_SH_OUT", "Shares outstanding (balance sheet)", "Balance Sheet", "Equity"),
    ("TANGIBLE_BV_PER_SH", "Tangible book value per share", "Balance Sheet", "Per Share"),
    ("TOTAL_CAPITAL", "Total capital (debt + equity)", "Balance Sheet", "Capital"),
    ("NET_WORTH", "Net worth (shareholders equity)", "Balance Sheet", "Equity"),

    # ===== CASH FLOW =====
    ("CF_DEPR_AMORT", "Depreciation & amortization (cash flow)", "Cash Flow", "Non-Cash"),
    ("CF_OPER_ACT", "Cash from operating activities", "Cash Flow", "Operating"),
    ("CF_INV_ACT", "Cash from investing activities", "Cash Flow", "Investing"),
    ("CF_FIN_ACT", "Cash from financing activities", "Cash Flow", "Financing"),
    ("CF_NET_CHANGE", "Net change in cash", "Cash Flow", "Summary"),
    ("CF_DIVIDENDS_PAID", "Dividends paid (cash flow statement)", "Cash Flow", "Financing"),
    ("CF_BUYBACKS", "Share buybacks/repurchases (cash flow)", "Cash Flow", "Financing"),
    ("CF_STOCK_ISSUANCE", "Stock issuance proceeds", "Cash Flow", "Financing"),
    ("LEVERED_FCF", "Levered free cash flow", "Cash Flow", "Free Cash Flow"),
    ("UNLEVERED_FCF", "Unlevered free cash flow", "Cash Flow", "Free Cash Flow"),

    # ===== FINANCIAL HEALTH / SOLVENCY =====
    ("CURRENT_RATIO", "Current ratio (current assets / current liabilities)", "Financial Health", "Liquidity"),
    ("QUICK_RATIO", "Quick ratio (acid test)", "Financial Health", "Liquidity"),
    ("DEBT_TO_EQUITY", "Debt-to-equity ratio", "Financial Health", "Leverage"),
    ("DEBT_TO_TOTAL_CAP", "Debt-to-total-capital ratio", "Financial Health", "Leverage"),
    ("INTEREST_COVERAGE_RATIO", "Interest coverage ratio (EBIT / interest)", "Financial Health", "Coverage"),
    ("FIXED_CHARGE_COVERAGE", "Fixed charge coverage ratio", "Financial Health", "Coverage"),
    ("SOLVENCY_RATIO", "Solvency ratio", "Financial Health", "Solvency"),
    ("LT_DEBT_TO_EQUITY", "Long-term debt to equity", "Financial Health", "Leverage"),
    ("CASH_CONVERSION_CYCLE", "Cash conversion cycle (days)", "Financial Health", "Efficiency"),
    ("NET_DEBT", "Net debt (total debt - cash)", "Financial Health", "Leverage"),

    # ===== EFFICIENCY =====
    ("SALES_PER_EMPLOYEE", "Revenue per employee", "Efficiency", "Per Employee"),
    ("NET_INCOME_PER_EMP", "Net income per employee", "Efficiency", "Per Employee"),
    ("EFFICIENCY_RATIO", "Efficiency ratio (banks: cost/income)", "Efficiency", "Banking"),
    ("RECEIVABLES_DAYS", "Days sales outstanding (DSO)", "Efficiency", "Turnover"),
    ("INVENTORY_DAYS", "Days inventory outstanding (DIO)", "Efficiency", "Turnover"),
    ("PAYABLES_DAYS", "Days payable outstanding (DPO)", "Efficiency", "Turnover"),
    ("CASH_CONV_CYC", "Cash conversion cycle (DSO + DIO - DPO)", "Efficiency", "Turnover"),

    # ===== ESG (mostly missing) =====
    ("BESG_SCORE", "Bloomberg ESG overall score (0-100)", "ESG", "Overall"),
    ("BESG_ENV_SCORE", "Bloomberg Environmental pillar score (0-100)", "ESG", "Environmental"),
    ("BESG_SOC_SCORE", "Bloomberg Social pillar score (0-100)", "ESG", "Social"),
    ("BESG_GOV_SCORE", "Bloomberg Governance pillar score (0-100)", "ESG", "Governance"),
    ("BESG_DISCLOSURE_SCORE", "Bloomberg ESG disclosure score", "ESG", "Disclosure"),
    ("CO2_TOTAL", "Total CO2 and CO2-equivalent emissions", "ESG", "Climate"),
    ("CO2_SCOPE1", "Scope 1 CO2 emissions (direct)", "ESG", "Climate"),
    ("CO2_SCOPE2", "Scope 2 CO2 emissions (purchased energy)", "ESG", "Climate"),
    ("CO2_SCOPE3", "Scope 3 CO2 emissions (supply chain)", "ESG", "Climate"),
    ("ENERGY_CONSUMPTION", "Total energy consumption (MWh)", "ESG", "Environmental"),
    ("WATER_WITHDRAWAL", "Total water withdrawal (cubic meters)", "ESG", "Environmental"),
    ("WASTE_TOTAL", "Total waste generated (metric tons)", "ESG", "Environmental"),
    ("BOARD_SIZE", "Board size (number of directors)", "ESG", "Governance"),
    ("BOARD_INDEPENDENCE", "Percentage of independent directors", "ESG", "Governance"),
    ("BOARD_DIVERSITY", "Percentage of women on board", "ESG", "Governance"),
    ("WOMEN_MID_MANAGEMENT_PCT", "Percentage of women in mid-management", "ESG", "Social"),
    ("SUSTAINABILITY_REPORTING", "Whether company issues sustainability report", "ESG", "Disclosure"),

    # ===== OWNERSHIP / SHORT INTEREST =====
    ("SHORT_RATIO", "Short interest ratio (days to cover)", "Ownership", "Short Interest"),
    ("SHORT_PCT_OF_FLOAT", "Short interest as % of float", "Ownership", "Short Interest"),
    ("DAYS_TO_COVER", "Days to cover short interest", "Ownership", "Short Interest"),
    ("INSIDER_HOLDINGS_PCT", "Percentage held by insiders", "Ownership", "Insider"),
    ("INSTITUTIONAL_HOLDINGS_PCT", "Percentage held by institutions", "Ownership", "Institutional"),
    ("INSTITUTIONAL_BUYING", "Institutional net buying (13F changes)", "Ownership", "Institutional"),
    ("INSTITUTIONAL_SELLING", "Institutional net selling (13F changes)", "Ownership", "Institutional"),
    ("FLOAT", "Public float (shares available for trading)", "Ownership", "Float"),
    ("FLOAT_PERCENT", "Public float as % of shares outstanding", "Ownership", "Float"),
    ("BORROW_FEE", "Stock borrow fee rate (%)", "Ownership", "Securities Lending"),
    ("BORROW_AVAILABLE", "Shares available to borrow", "Ownership", "Securities Lending"),
    ("UTILIZATION_PCT", "Securities lending utilization percentage", "Ownership", "Securities Lending"),

    # ===== ETF-SPECIFIC =====
    ("ETF_NAV", "Net asset value of the ETF per share", "ETF", "NAV"),
    ("NAV_PREMIUM", "Premium/discount of market price to NAV (absolute)", "ETF", "NAV"),
    ("NAV_PREMIUM_PCT", "Premium/discount of market price to NAV (%)", "ETF", "NAV"),
    ("FUND_INCEPTION_DATE", "Fund inception date", "ETF", "Fund Info"),
    ("FUND_MANAGER", "Fund manager name", "ETF", "Fund Info"),
    ("FUND_MGR_STATED_FEE", "Fund management fee (stated)", "ETF", "Fees"),
    ("EXPENSE_RATIO", "Expense ratio", "ETF", "Fees"),
    ("EXPENSE_RATIO_NET", "Net expense ratio after waivers", "ETF", "Fees"),
    ("HOLDINGS_COUNT", "Number of holdings in the fund", "ETF", "Holdings"),
    ("TOP10_HOLDINGS_PCT", "% of assets in top 10 holdings", "ETF", "Holdings"),
    ("TRACKING_ERROR", "Tracking error vs benchmark (3-year annualized)", "ETF", "Performance"),
    ("TRACKING_DIFFERENCE", "Tracking difference vs benchmark (1-year)", "ETF", "Performance"),
    ("BETA_FUND", "Fund beta (3-year)", "ETF", "Risk"),
    ("STD_DEV_FUND", "Fund standard deviation (3-year annualized)", "ETF", "Risk"),
    ("SHARPE_FUND", "Fund Sharpe ratio (3-year)", "ETF", "Risk/Reward"),
    ("ALPHA_FUND", "Fund alpha (3-year annualized)", "ETF", "Performance"),
    ("R2_FUND", "Fund R-squared (3-year)", "ETF", "Risk"),
    ("FUND_CATEGORY", "Fund category/classification", "ETF", "Fund Info"),
    ("FUND_30D_YIELD", "Fund 30-day SEC yield", "ETF", "Yield"),
    ("FUND_DISTRIBUTION_YIELD", "Fund distribution yield", "ETF", "Yield"),
    ("FUND_12M_YIELD", "Fund trailing 12-month yield", "ETF", "Yield"),
    ("AVG_DAILY_VOLUME_ETF", "ETF average daily trading volume", "ETF", "Liquidity"),
    ("BID_ASK_SPREAD_ETF", "ETF bid-ask spread (bps)", "ETF", "Liquidity"),
    ("CREATION_UNIT_SIZE", "ETF creation unit size (shares)", "ETF", "Creation/Redemption"),
    ("ESTIMATED_CASH", "ETF estimated cash component per creation unit", "ETF", "Creation/Redemption"),
    ("ETF_FLOW_1D", "ETF net flow (1-day, $mm)", "ETF", "Flows"),
    ("ETF_FLOW_MTD", "ETF net flow (month-to-date, $mm)", "ETF", "Flows"),
    ("ETF_FLOW_YTD", "ETF net flow (year-to-date, $mm)", "ETF", "Flows"),
    ("ETF_AUM", "ETF total assets under management ($mm)", "ETF", "AUM"),
    ("AUM_CHANGE_1D", "ETF AUM change (1-day, $mm)", "ETF", "AUM"),
    ("AUM_CHANGE_MTD", "ETF AUM change (month-to-date, $mm)", "ETF", "AUM"),
    ("ETF_IN_KIND_CREATION", "ETF in-kind creation amount ($mm)", "ETF", "Creation/Redemption"),
    ("ETF_IN_KIND_REDEMPTION", "ETF in-kind redemption amount ($mm)", "ETF", "Creation/Redemption"),

    # ===== INDEX-SPECIFIC =====
    ("INDX_MEMBERS", "Index constituents list (BDS field)", "Index", "Constituents"),
    ("INDX_MWEIGHT", "Index member weights (BDS field, %)", "Index", "Weights"),
    ("INDX_DIVISOR", "Index divisor", "Index", "Methodology"),
    ("INDX_TOTAL_RETURN", "Index total return level (with dividends)", "Index", "Returns"),
    ("INDX_NET_RETURN", "Index net return level (with net dividends)", "Index", "Returns"),
    ("INDX_PRICE_RETURN", "Index price return level", "Index", "Returns"),
    ("INDX_MARKET_CAP", "Index total market capitalization", "Index", "Characteristics"),
    ("INDX_DIVIDEND_YIELD", "Index dividend yield", "Index", "Characteristics"),
    ("INDX_PE_RATIO", "Index PE ratio", "Index", "Characteristics"),
    ("INDX_PB_RATIO", "Index price-to-book ratio", "Index", "Characteristics"),
    ("INDX_COUNT", "Number of constituents in index", "Index", "Characteristics"),
    ("INDX_TOP_10_WEIGHT", "Weight of top 10 constituents (%)", "Index", "Concentration"),
    ("INDX_HERFINDAHL", "Herfindahl concentration index", "Index", "Concentration"),
    ("INDX_52W_HIGH", "Index 52-week high", "Index", "Price"),
    ("INDX_52W_LOW", "Index 52-week low", "Index", "Price"),
    ("INDX_AVG_VOLUME", "Index average daily volume", "Index", "Volume"),
    ("INDX_SECTOR_BREAKDOWN", "Index sector weight breakdown (BDS)", "Index", "Composition"),

    # ===== OPTIONS / DERIVATIVES =====
    ("CHAIN_TICKERS", "Option chain tickers (BDS, with overrides)", "Options", "Chain"),
    ("OPT_DELTA", "Option delta (rate of change w.r.t. underlying)", "Options", "Greeks"),
    ("OPT_GAMMA", "Option gamma (rate of change of delta)", "Options", "Greeks"),
    ("OPT_THETA", "Option theta (time decay per day)", "Options", "Greeks"),
    ("OPT_VEGA", "Option vega (volatility sensitivity)", "Options", "Greeks"),
    ("OPT_RHO", "Option rho (interest rate sensitivity)", "Options", "Greeks"),
    ("OPT_IMPVOL", "Option implied volatility", "Options", "Volatility"),
    ("OPT_STRIKE", "Option strike price", "Options", "Contract Terms"),
    ("OPT_EXPIRE_DT", "Option expiration date", "Options", "Contract Terms"),
    ("OPT_PUT_CALL", "Option type (Put or Call)", "Options", "Contract Terms"),
    ("OPT_OPEN_INT", "Option open interest", "Options", "Volume/Open Interest"),
    ("OPT_VOLUME", "Option trading volume", "Options", "Volume/Open Interest"),
    ("OPT_UNDERLYING_PX", "Option underlying security price", "Options", "Pricing"),
    ("IMPLIED_VOL_30D", "30-day at-the-money implied volatility", "Options", "Volatility"),
    ("IMPLIED_VOL_60D", "60-day at-the-money implied volatility", "Options", "Volatility"),
    ("IMPLIED_VOL_90D", "90-day at-the-money implied volatility", "Options", "Volatility"),
    ("PUT_CALL_RATIO", "Put/call ratio (volume)", "Options", "Sentiment"),
    ("SKEW_30D", "30-day implied volatility skew (25D put - 25D call)", "Options", "Skew"),

    # ===== CORPORATE ACTIONS =====
    ("EQY_DVD_AMT", "Dividend amount per share", "Corporate Actions", "Dividends"),
    ("EQY_DVD_FREQ", "Dividend frequency (annual, quarterly, monthly, etc.)", "Corporate Actions", "Dividends"),
    ("EQY_DVD_TYPE", "Dividend type (regular, special, stock)", "Corporate Actions", "Dividends"),
    ("EQY_DVD_EX_DT", "Dividend ex-date", "Corporate Actions", "Dividends"),
    ("EQY_DVD_REC_DT", "Dividend record date", "Corporate Actions", "Dividends"),
    ("EQY_DVD_PAY_DT", "Dividend payable date", "Corporate Actions", "Dividends"),
    ("SPLIT_RATIO", "Stock split ratio (e.g., 4:1)", "Corporate Actions", "Splits"),
    ("SPLIT_DATE", "Stock split date", "Corporate Actions", "Splits"),
    ("EQY_INIT_PX", "IPO price", "Corporate Actions", "IPO"),
    ("EQY_INIT_DATE", "IPO date", "Corporate Actions", "IPO"),
    ("EQY_FOUNDING_DATE", "Company founding date", "Corporate Actions", "IPO"),
    ("NEXT_EARNINGS_DATE", "Next earnings announcement date", "Corporate Actions", "Earnings"),
    ("STOCK_DIVIDEND_PCT", "Stock dividend percentage", "Corporate Actions", "Dividends"),

    # ===== DESCRIPTIVE / REFERENCE (several missing) =====
    ("SECURITY_NAME", "Full security/company name", "Descriptive", "Names"),
    ("SECURITY_TYP", "Security type (Equity, Bond, ETF, etc.)", "Descriptive", "Classification"),
    ("EQY_FUND_CRNCY", "Fundamental reporting currency", "Descriptive", "Currency"),
    ("GICS_SECTOR_NAME", "GICS sector name", "Descriptive", "Classification"),
    ("GICS_INDUSTRY_NAME", "GICS industry name", "Descriptive", "Classification"),
    ("GICS_SUB_INDUSTRY_NAME", "GICS sub-industry name", "Descriptive", "Classification"),
    ("PRIMARY_EXCHANGE", "Primary exchange code", "Descriptive", "Exchange"),
    ("PRIMARY_TICKER", "Primary Bloomberg ticker", "Descriptive", "Identifiers"),
    ("ID_BB", "Bloomberg unique ID (internal)", "Descriptive", "Identifiers"),
    ("ID_BB_GLOBAL", "Bloomberg Global ID (BBGID)", "Descriptive", "Identifiers"),
    ("ID_BB_COMPANY", "Bloomberg company ID", "Descriptive", "Identifiers"),
    ("FIGI", "Financial Instrument Global Identifier", "Descriptive", "Identifiers"),
    ("MIC", "Market Identifier Code", "Descriptive", "Exchange"),
    ("MKTCAP_RANK", "Market capitalization rank", "Descriptive", "Ranking"),
    ("FISCAL_YEAR_END", "Fiscal year end month", "Descriptive", "Dates"),
    ("MARKET_STATUS", "Market status (Open/Closed)", "Descriptive", "Trading"),
    ("TIME_ZONE", "Exchange timezone", "Descriptive", "Trading"),
    ("ADDRESS_OF_ISSUER", "Issuer address", "Descriptive", "Legal"),
    ("PHONE_NUMBER", "Issuer phone number", "Descriptive", "Legal"),
    ("WEBSITE", "Company website URL", "Descriptive", "Legal"),
    ("COMMON_STOCK_TICKER", "Common stock ticker (for ADR/preferred)", "Descriptive", "Cross-Reference"),
    ("ADR_RATIO", "ADR ratio (underlying shares per ADR)", "Descriptive", "Cross-Reference"),

    # ===== COMMODITY-SPECIFIC =====
    ("FUT_DAYS_EXP", "Futures days to expiration", "Commodities/Futures", "Expiration"),
    ("FUT_EXPIRATION_DT", "Futures expiration date", "Commodities/Futures", "Expiration"),
    ("FUT_OPEN_INT", "Futures open interest", "Commodities/Futures", "Volume"),
    ("FUT_CONTRACT_SIZE", "Futures contract size", "Commodities/Futures", "Contract Terms"),
    ("FUT_POINT_VALUE", "Futures point value ($ per point)", "Commodities/Futures", "Contract Terms"),
    ("FUT_TICK_SIZE", "Futures minimum price increment", "Commodities/Futures", "Contract Terms"),
    ("FUT_TICK_VALUE", "Futures tick value ($ per tick)", "Commodities/Futures", "Contract Terms"),
    ("FUT_BASIS", "Futures basis (spot - futures price)", "Commodities/Futures", "Basis"),
    ("FUT_CARRY", "Futures annualized carry", "Commodities/Futures", "Basis"),

    # ===== MACRO / ECONOMIC =====
    ("CDS_SPREAD_5Y", "5-year CDS spread (bps)", "Macro / Fixed Income", "Credit"),
    ("CDS_SPREAD_10Y", "10-year CDS spread (bps)", "Macro / Fixed Income", "Credit"),
    ("YAS_BOND_YLD", "Bond yield to maturity (YAS calculator)", "Macro / Fixed Income", "Bond Analytics"),
    ("YAS_MOD_DUR", "Modified duration (YAS calculator)", "Macro / Fixed Income", "Bond Analytics"),
    ("YAS_OAS_SPRD", "Option-adjusted spread (YAS calculator)", "Macro / Fixed Income", "Bond Analytics"),
    ("YAS_Z_SPREAD", "Zero-volatility spread (YAS calculator)", "Macro / Fixed Income", "Bond Analytics"),
    ("YAS_CONVEXITY", "Bond convexity (YAS calculator)", "Macro / Fixed Income", "Bond Analytics"),
    ("YAS_DV01", "Dollar value of 1bp change (YAS)", "Macro / Fixed Income", "Bond Analytics"),
    ("YAS_YTC", "Yield to call (YAS calculator)", "Macro / Fixed Income", "Bond Analytics"),
    ("YAS_YTP", "Yield to put (YAS calculator)", "Macro / Fixed Income", "Bond Analytics"),

    # ===== REAL ESTATE / REIT =====
    ("FFO", "Funds From Operations (REITs)", "REIT", "Performance"),
    ("FFO_PER_SHARE", "Funds From Operations per share", "REIT", "Per Share"),
    ("AFFO", "Adjusted Funds From Operations", "REIT", "Performance"),
    ("NOI", "Net Operating Income (property level)", "REIT", "Property"),
    ("CAP_RATE", "Capitalization rate (implied)", "REIT", "Valuation"),
    ("OCCUPANCY_RATE", "Property occupancy rate (%)", "REIT", "Property"),
    ("SAME_STORE_SALES_GROWTH", "Same-store sales growth (REITs/retail)", "REIT", "Growth"),
    ("NAV_PER_SHARE_REIT", "Net asset value per share (REIT)", "REIT", "Valuation"),
    ("P_FFO", "Price to Funds From Operations ratio", "REIT", "Valuation"),

    # ===== MISCELLANEOUS / ADVANCED =====
    ("WACC", "Weighted average cost of capital", "Advanced", "Valuation"),
    ("ECONOMIC_VALUE_ADDED", "Economic Value Added (EVA)", "Advanced", "Performance"),
    ("TOTAL_SHAREHOLDER_RETURN", "Total shareholder return (price + dividends)", "Advanced", "Returns"),
    ("CUM_RETURN_1YR", "Cumulative 1-year total return", "Advanced", "Returns"),
    ("CUM_RETURN_3YR", "Cumulative 3-year total return", "Advanced", "Returns"),
    ("CUM_RETURN_5YR", "Cumulative 5-year total return", "Advanced", "Returns"),
    ("DIVIDEND_REINVESTMENT", "Dividend reinvestment plan indicator", "Advanced", "Dividends"),
    ("DIVIDEND_REINVEST_DATE", "DRIP ex-date", "Advanced", "Dividends"),
]


def main():
    print(f"Reading existing catalog from: {CATALOG_PATH}")
    df_existing = pd.read_excel(CATALOG_PATH, sheet_name=SHEET_NAME)
    existing_fields = set()
    for _, row in df_existing.iterrows():
        val = row.iloc[1]  # Column B = "Display Name"
        if pd.notna(val):
            existing_fields.add(str(val).strip().upper())

    print(f"Existing unique field mnemonics: {len(existing_fields)}")

    # Build combined catalog
    rows = []
    seen = set(existing_fields)  # Track all fields to avoid duplicates

    # First add all existing fields from the master list with their categories
    # We need to categorise the existing ones too
    print("\nCategorizing existing fields...")
    
    category_lookup = {
        "Price & Volume": ["PX_", "PRICE", "HIGH", "LOW", "OPEN", "CLOSE", "VOLUME", "TURNOVER",
                          "VWAP", "TRADE", "BID", "ASK", "SPREAD", "LAST", "CHANGE", "RETURN",
                          "ADVANC", "DECLINE", "TICK", "TRDVOL", "AVRG"],
        "Valuation": ["PE_", "PB_", "PS_", "PCF", "EV_", "PRICE_TO_BOOK", "PRICE_TO_EARN",
                      "PRICE_TO_SALE", "PRICE_TO_CASH", "DIV_YIELD", "DVD_YIELD", "DIVIDEND",
                      "YIELD", "ENTERPRISE_VALUE", "MARKET_CAP", "MKT_CAP", "CUR_MKT_CAP",
                      "FCF_YIELD", "EARNINGS_YIELD", "CAPE", "DVD_YLD"],
        "Profitability": ["PROFIT_MARGIN", "MARGIN", "ROE", "ROA", "ROCE", "ROIC",
                          "RETURN_ON_", "RETURN_COM_EQY", "EBITDA", "EBIT", "NET_INCOME",
                          "NOPAT", "GROSS_PROFIT"],
        "Growth": ["GROWTH", "MOMENTUM", "EPS_GROW", "DRIV", "LONG_TERM_GROWTH"],
        "Financial Health": ["DEBT", "LEVERAGE", "COVERAGE", "LIQUIDITY", "QUICK_RATIO",
                            "CURRENT_RATIO", "SOLVENCY", "NET_DEBT"],
        "Cash Flow": ["CASH_FLOW", "FCF", "FREE_CASH", "OPERATING_CF", "CAPEX", "CF_",
                      "CASH_FROM_OPS", "CAPITAL_EXPEND"],
        "Efficiency": ["TURNOVER", "DAYS_", "EFFICIENCY", "ASSET_TURN"],
        "Technical": ["MOV_AVG", "MOVING_AVERAGE", "SMA_", "AVG_TRUE_RANGE", "ATR",
                      "VOLATILITY_", "BETA_", "ALPHA_", "RSQUARED", "RSI", "MACD",
                      "BOLLINGER", "STOCHASTIC", "ADX", "CCI", "MFI", "OBV",
                      "WILLIAM", "WILLIAMS", "AROON", "CHAIKIN", "TRAIL_",
                      "TOTAL_RETURN_INDEX", "CORRELATION", "SKEWNESS", "KURTOSIS",
                      "VAR_", "TAIL_RISK"],
        "Estimates": ["BEST_", "ESTIMATE", "CONSENSUS", "TARGET_PRICE", "RECOMMEND",
                      "NUM_EST", "FORWARD_", "TRAIL_12M_EPS", "TRAIL_12M_SALES",
                      "NUM_UPGRADES", "NUM_DOWNGRADES", "SURPRISE"],
        "ESG": ["ESG", "ENVIRONMENT", "SOCIAL", "GOVERNANCE", "SUSTAINABIL", "CARBON",
                "EMISSION", "CO2_", "ENERGY_CONSUMP", "WATER_", "WASTE_", "BOARD_",
                "WOMEN_"],
        "Ownership": ["SHORT_", "FLOAT", "INSIDER_", "INSTITUTIONAL_", "BORROW_",
                      "UTILIZATION", "SHARES_OUT", "AVERAGE_VOLUME"],
        "ETF": ["ETF_", "NAV_", "PREMIUM", "DISCOUNT", "EXPENSE_RATIO", "HOLDINGS_",
                "TRACKING_", "FUND_", "AUM", "CREATION_", "REDEMPTION", "BID_ASK_SPREAD",
                "FUND_MANAGER", "FUND_CATEGORY", "FUND_INCEPTION"],
        "Index": ["INDX_", "INDEX_", "CONSTITUENT", "MEMBERSHIP"],
        "Options": ["OPT_", "IMPLIED_VOL", "IMPVOL", "PUT_CALL", "SKEW_", "CHAIN_",
                    "DELTA", "GAMMA", "VEGA", "THETA", "RHO"],
        "Corporate Actions": ["SPLIT", "BUYBACK", "REPURCHASE", "EQY_DVD_", "DVD_",
                              "EQY_INIT_", "IPO"],
        "Descriptive": ["NAME", "TICKER", "SEDOL", "CUSIP", "ISIN", "FIGI", "SECURITY_",
                        "SECTOR", "INDUSTRY", "GICS_", "COUNTRY", "EXCHANGE", "CRNCY",
                        "MIC", "PRIMARY_"],
        "Balance Sheet": ["BS_", "TOT_ASSET", "TOT_LIAB", "BOOK_VAL", "WORKING_CAPITAL",
                         "TANGIBLE_BV", "TOTAL_CAPITAL", "NET_WORTH", "SHAREHOLDER_EQUITY",
                         "MINORITY_INTEREST", "PREFERRED_STOCK", "TREASURY_STOCK",
                         "RETAINED_EARNINGS", "GOODWILL", "INTANGIBLE_ASSETS", "PPE",
                         "INVENTORY", "RECEIVABLES", "PAYABLES"],
        "Commodities/Futures": ["FUT_", "COMDTY", "COMMOD"],
        "Macro / Fixed Income": ["CDS_", "YAS_", "BOND", "YIELD_", "DURATION", "CONVEXITY",
                                 "COUPON", "MATURITY", "OAS_", "SPREAD_", "DV01"],
        "REIT": ["FFO_", "FUNDS_FROM_OPS", "AFFO", "NOI", "CAP_RATE", "OCCUPANCY",
                 "SAME_STORE"],
        "Advanced": ["WACC", "ECONOMIC_VALUE", "EVA", "CUM_RETURN", "TOTAL_SHAREHOLDER_RETURN",
                     "DRIP", "DIVIDEND_REINVEST"],
    }

    # Process existing fields
    for _, row in df_existing.iterrows():
        field_id = row.iloc[0]  # Column A = "Field ID"
        field_name = row.iloc[1]  # Column B = "Display Name"
        description = row.iloc[2] if pd.notna(row.iloc[2]) else ""  # Column C = "Description"
        data_type = row.iloc[3] if pd.notna(row.iloc[3]) else ""  # Column D = "Data Type"
        
        if pd.isna(field_name) or not str(field_name).strip():
            continue
        
        field_name = str(field_name).strip()
        field_upper = field_name.upper()
        description = str(description).strip() if description else ""
        
        # Determine category
        category = "Uncategorized"
        for cat_name, keywords in category_lookup.items():
            for kw in keywords:
                if kw in field_upper:
                    category = cat_name
                    break
            if category != "Uncategorized":
                break
        
        rows.append({
            "Field Mnemonic": field_name,
            "Category": category,
            "Description": description,
            "Data Type": data_type,
            "Status": "Existing",
            "Source": "Master Field List",
            "Existing Field ID": field_id if pd.notna(field_id) else ""
        })

    # Now add NEW fields that don't already exist
    print(f"\nAdding new fields from research...")
    new_count = 0
    for field_name, description, category, sub_category in NEW_FIELDS:
        field_upper = field_name.upper()
        if field_upper not in existing_fields:
            rows.append({
                "Field Mnemonic": field_name,
                "Category": f"{category} > {sub_category}",
                "Description": description,
                "Data Type": "",
                "Status": "NEW - Not Tested",
                "Source": "Web Research / Bloomberg Docs",
                "Existing Field ID": ""
            })
            new_count += 1
        else:
            # It already exists - update one of the existing entries to show the sub-category
            pass  # Skip - already in the list above

    print(f"New fields added: {new_count}")

    # Build DataFrame
    df_out = pd.DataFrame(rows)
    
    # Sort: Existing first (by category), then New
    df_out["_sort"] = df_out["Status"].map({"Existing": 0, "NEW - Not Tested": 1})
    df_out = df_out.sort_values(["_sort", "Category", "Field Mnemonic"]).drop(columns=["_sort"])

    # Write to Excel with formatting
    print(f"\nWriting to: {OUTPUT_PATH}")
    with pd.ExcelWriter(OUTPUT_PATH, engine='xlsxwriter') as writer:
        # Main catalog sheet
        df_out.to_excel(writer, sheet_name='Expanded Catalog', index=False)
        
        # Summary sheet
        summary_data = []
        
        # Count by category for existing
        existing_df = df_out[df_out["Status"] == "Existing"]
        new_df = df_out[df_out["Status"] != "Existing"]
        
        # Category totals
        all_categories = set()
        for cat in df_out["Category"].unique():
            parts = str(cat).split(" > ")
            all_categories.add(parts[0])
        
        # Per-category breakdown
        for cat in sorted(all_categories):
            existing_count = len(existing_df[existing_df["Category"].str.startswith(cat, na=False)])
            new_count_cat = len(new_df[new_df["Category"].str.startswith(cat, na=False)])
            summary_data.append({
                "Category": cat,
                "Existing Fields": existing_count,
                "New Additions": new_count_cat,
                "Total": existing_count + new_count_cat
            })
        
        # Total row
        summary_data.append({
            "Category": "TOTAL",
            "Existing Fields": len(existing_df),
            "New Additions": len(new_df),
            "Total": len(df_out)
        })
        
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='Category Summary', index=False)
        
        # New fields only sheet
        new_df.to_excel(writer, sheet_name='New Additions Only', index=False)
        
        # Formatting
        workbook = writer.book
        header_fmt = workbook.add_format({
            'bold': True, 'font_size': 11, 'bg_color': '#1F4E79',
            'font_color': 'white', 'border': 1
        })
        new_fmt = workbook.add_format({'bg_color': '#E2EFDA'})  # light green for new
        existing_fmt = workbook.add_format({'bg_color': '#FFFFFF'})
        
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            
            # Find the last column
            if sheet_name == "Expanded Catalog":
                worksheet.set_column('A:A', 30)  # Field Mnemonic
                worksheet.set_column('B:B', 35)  # Category
                worksheet.set_column('C:C', 60)  # Description
                worksheet.set_column('D:D', 15)  # Data Type
                worksheet.set_column('E:E', 22)  # Status
                worksheet.set_column('F:F', 30)  # Source
                worksheet.set_column('G:G', 20)  # Existing Field ID
                worksheet.autofilter(0, 0, len(df_out), 6)
                
                # Write header
                for col_num, value in enumerate(df_out.columns.values):
                    worksheet.write(0, col_num, value, header_fmt)
            elif sheet_name == "Category Summary":
                worksheet.set_column('A:A', 30)
                worksheet.set_column('B:D', 18)
                for col_num, value in enumerate(df_summary.columns.values):
                    worksheet.write(0, col_num, value, header_fmt)
            elif sheet_name == "New Additions Only":
                worksheet.set_column('A:A', 30)
                worksheet.set_column('B:B', 35)
                worksheet.set_column('C:C', 60)
                worksheet.set_column('E:E', 22)
                for col_num, value in enumerate(new_df.columns.values):
                    worksheet.write(0, col_num, value, header_fmt)
    
    print(f"\n{'='*60}")
    print(f"EXPANDED FIELD CATALOG COMPLETE")
    print(f"{'='*60}")
    print(f"Existing fields: {len(existing_df)}")
    print(f"New additions:   {len(new_df)}")
    print(f"Total catalog:   {len(df_out)}")
    print(f"\nOutput file: {OUTPUT_PATH}")
    print(f"\nSheets:")
    print(f"  1. Expanded Catalog - All fields with categories and status")
    print(f"  2. Category Summary - Counts by domain")
    print(f"  3. New Additions Only - Just the new fields for easy review")
    print(f"\nNOTE: New fields marked 'NEW - Not Tested' need to be verified")
    print(f"against Bloomberg before use in production.")


if __name__ == "__main__":
    main()

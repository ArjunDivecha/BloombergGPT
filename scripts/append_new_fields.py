"""
=============================================================================
SCRIPT NAME: append_new_fields.py
=============================================================================

INPUT FILES:
- Production Data/Bloomberg Master Field List.xlsx: Existing field catalog
  Sheet: "Pruned List" with columns: Field ID, Display Name, Description, Data Type,
  MXEF Index, INDA Equity, AAPL US Equity, SPX Index, CL1 Comdty, EURUSD Curncy,
  USGG10YR Index

OUTPUT FILES:
- Production Data/Bloomberg Master Field List.xlsx: Updated with new fields
  appended at the bottom of the "Pruned List" sheet

VERSION: 1.0
LAST UPDATED: 2026-04-27

DESCRIPTION:
Appends 278 new Bloomberg fields (from web research and Bloomberg docs) to
the bottom of the existing Bloomberg Master Field List.xlsx. Each new field
preserves the existing column structure — Field ID, Display Name, Description,
Data Type, and coverage columns (all empty for the new fields since they
haven't been tested yet).

DEPENDENCIES:
- pandas, openpyxl

USAGE:
cd /Users/arjundivecha/Dropbox/AAA\ Backup/A\ Working/BloombergGPT
python scripts/append_new_fields.py

NOTES:
- New fields are appended, not inserted, so existing data is untouched
- Coverage columns are left blank for new fields (marked "untested")
- Run this script AFTER confirming the existing file is backed up
=============================================================================
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import shutil
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
CATALOG_PATH = BASE_DIR / "Production Data" / "Bloomberg Master Field List.xlsx"
SHEET_NAME = "Pruned List"

# ── New fields to add ──────────────────────────────────────────────
NEW_FIELDS = [
    # Technical - Moving Averages
    ("PX_AVERAGE_20D", "20-day average price", "Price"),
    ("PX_AVERAGE_50D", "50-day average price", "Price"),
    ("PX_AVERAGE_200D", "200-day average price", "Price"),
    ("SMAX_50D", "Current price distance from 50-day SMA (percent)", "Derived"),
    ("SMAX_200D", "Current price distance from 200-day SMA (percent)", "Derived"),

    # Technical - RSI / Momentum
    ("RSI_INDEX_14D", "14-day Relative Strength Index (RSI)", "Derived"),
    ("WILLIAMS_R_14D", "14-day Williams %R oscillator", "Derived"),
    ("CCI_20D", "20-day Commodity Channel Index", "Derived"),
    ("AROON_UP_14D", "14-day Aroon Up indicator", "Derived"),
    ("AROON_DOWN_14D", "14-day Aroon Down indicator", "Derived"),

    # Technical - MACD
    ("MACD", "Moving Average Convergence Divergence (MACD line)", "Derived"),
    ("MACD_SIGNAL", "MACD signal line (9-day EMA of MACD)", "Derived"),
    ("MACD_HISTOGRAM", "MACD histogram (MACD minus signal line)", "Derived"),

    # Technical - Bollinger Bands
    ("BOLLINGER_UPPER", "Upper Bollinger Band (20-day SMA plus 2 standard deviations)", "Derived"),
    ("BOLLINGER_LOWER", "Lower Bollinger Band (20-day SMA minus 2 standard deviations)", "Derived"),
    ("BOLLINGER_MIDDLE", "Middle Bollinger Band (20-day simple moving average)", "Derived"),

    # Technical - Stochastic
    ("STOCHASTIC_14D", "14-day stochastic oscillator percentK", "Derived"),

    # Technical - Volatility
    ("AVG_TRUE_RANGE_14D", "14-day average true range (ATR)", "Derived"),
    ("VOLATILITY_30D", "30-day historical volatility (annualized percent)", "Derived"),
    ("VOLATILITY_60D", "60-day historical volatility (annualized percent)", "Derived"),
    ("VOLATILITY_90D", "90-day historical volatility (annualized percent)", "Derived"),
    ("VOLATILITY_180D", "180-day historical volatility (annualized percent)", "Derived"),
    ("VOLATILITY_1YR", "1-year historical volatility (annualized percent)", "Derived"),

    # Technical - ADX / DMI
    ("ADX_14D", "14-day Average Directional Index", "Derived"),
    ("DI_PLUS_14D", "14-day Plus Directional Indicator (+DI)", "Derived"),
    ("DI_MINUS_14D", "14-day Minus Directional Indicator (-DI)", "Derived"),

    # Technical - Volume-based
    ("OBV", "On-Balance Volume", "Derived"),
    ("MFI_14D", "14-day Money Flow Index", "Derived"),
    ("CHAIKIN_OSCILLATOR", "Chaikin Oscillator", "Derived"),

    # Technical - Returns
    ("TOTAL_RETURN_INDEX", "Total return index (price plus dividends reinvested)", "Derived"),
    ("TRAIL_1M_RETURN", "Trailing 1-month price return (percent)", "Derived"),
    ("TRAIL_3M_RETURN", "Trailing 3-month price return (percent)", "Derived"),
    ("TRAIL_6M_RETURN", "Trailing 6-month price return (percent)", "Derived"),
    ("TRAIL_12M_RETURN", "Trailing 12-month price return (percent)", "Derived"),
    ("TRAIL_1M_TOTAL_RETURN", "Trailing 1-month total return with dividends (percent)", "Derived"),
    ("TRAIL_3M_TOTAL_RETURN", "Trailing 3-month total return with dividends (percent)", "Derived"),
    ("TRAIL_6M_TOTAL_RETURN", "Trailing 6-month total return with dividends (percent)", "Derived"),
    ("TRAIL_12M_TOTAL_RETURN", "Trailing 12-month total return with dividends (percent)", "Derived"),

    # Risk - Beta / Alpha
    ("BETA_RAW", "Raw beta vs S&P 500 (2-year weekly regression)", "Derived"),
    ("BETA_ADJUSTED", "Adjusted beta (Bloomberg adjusted beta)", "Derived"),
    ("ALPHA_RAW", "Raw alpha from beta regression (excess return)", "Derived"),
    ("RSQUARED", "R-squared from beta regression", "Derived"),

    # Risk - Ratios
    ("TREYNOR_RATIO", "Treynor ratio (excess return divided by beta)", "Derived"),
    ("SORTINO_RATIO", "Sortino ratio (uses downside deviation only)", "Derived"),

    # Risk - Distribution / Drawdown
    ("MAX_DRAWDOWN_12M", "Maximum drawdown over trailing 12 months (percent)", "Derived"),
    ("SKEWNESS_1YR", "1-year return skewness", "Derived"),
    ("KURTOSIS_1YR", "1-year return kurtosis", "Derived"),

    # Risk - VaR
    ("VAR_95_1D", "Value at Risk 95 percent confidence 1-day", "Derived"),
    ("TAIL_RISK_95", "Tail risk / Conditional VaR at 95 percent confidence", "Derived"),

    # Risk - Correlation
    ("CORRELATION_SPX_1YR", "1-year correlation with S&P 500", "Derived"),

    # Valuation - PE-based
    ("FORWARD_PE_RATIO", "Forward price-to-earnings ratio (next 12 months)", "Derived"),
    ("TRAIL_PE_RATIO", "Trailing price-to-earnings ratio (trailing 12 months)", "Derived"),
    ("CAPE_RATIO", "Cyclically adjusted price-to-earnings ratio (Shiller PE)", "Derived"),

    # Valuation - Multiples
    ("PX_TO_EBITDA", "Price-to-EBITDA ratio", "Derived"),
    ("PX_TO_CASH_FLOW", "Price-to-cash flow ratio", "Derived"),

    # Valuation - EV Multiples
    ("EV_TO_SALES", "Enterprise value divided by revenue", "Derived"),
    ("EV_TO_EBIT", "Enterprise value divided by EBIT", "Derived"),
    ("EV_TO_INVESTED_CAPITAL", "Enterprise value divided by invested capital", "Derived"),

    # Valuation - Yield-based
    ("EARNINGS_YIELD", "Earnings yield (EPS divided by price, inverse of PE)", "Derived"),
    ("FCF_YIELD", "Free cash flow yield (FCF divided by market cap)", "Derived"),
    ("SALES_YIELD", "Sales yield (revenue divided by market cap)", "Derived"),

    # Profitability - Margins
    ("FCF_MARGIN", "Free cash flow margin (FCF divided by revenue, percent)", "Derived"),
    ("EBITDA_MARGIN", "EBITDA margin (EBITDA divided by revenue, percent)", "Derived"),
    ("EBIT_MARGIN", "EBIT margin (EBIT divided by revenue, percent)", "Derived"),
    ("PRETAX_MARGIN", "Pre-tax profit margin (pretax income divided by revenue)", "Derived"),

    # Profitability - Absolute
    ("GROSS_PROFIT", "Gross profit (revenue minus cost of goods sold)", "BS085"),  # has BS/IS internal ID
    ("NOPAT", "Net operating profit after tax", "Derived"),

    # Profitability - Returns
    ("RETURN_ON_INV_CAP", "Return on invested capital (ROIC)", "Derived"),

    # Growth - EPS Growth
    ("BEST_EPS_GROWTH", "Consensus EPS growth rate for next fiscal year", "Derived"),
    ("BEST_LT_EPS_GROWTH", "Consensus long-term EPS growth rate (3-5 year)", "Derived"),

    # Growth - Sales Growth
    ("BEST_SALES_GROWTH", "Consensus sales/revenue growth rate", "Derived"),

    # Growth - Historical Growth
    ("5Y_SALES_GROWTH", "5-year compounded annual sales growth rate", "Derived"),
    ("5Y_EPS_GROWTH", "5-year compounded annual EPS growth rate", "Derived"),
    ("5Y_DVD_GROWTH", "5-year compounded annual dividend growth rate", "Derived"),

    # Growth - Fundamental
    ("SUSTAINABLE_GROWTH", "Sustainable growth rate (ROE times retention ratio)", "Derived"),
    ("REINVESTMENT_RATE", "Reinvestment rate (1 minus payout ratio)", "Derived"),

    # Estimates - EPS / Revenue
    ("FORWARD_12M_EPS", "Forward 12-month EPS (derived from consensus)", "Derived"),
    ("FORWARD_12M_SALES", "Forward 12-month sales estimate", "Derived"),

    # Estimates - Target Price
    ("BEST_TARGET_PRICE_HIGH", "Highest analyst price target", "Derived"),
    ("BEST_TARGET_PRICE_LOW", "Lowest analyst price target", "Derived"),

    # Estimates - Profitability
    ("BEST_EBITDA", "Consensus EBITDA estimate", "Derived"),
    ("BEST_NET_INCOME", "Consensus net income estimate", "Derived"),
    ("BEST_DPS", "Consensus dividend per share estimate", "Derived"),

    # Estimates - Coverage
    ("NUM_ESTIMATES", "Number of analyst estimates contributing to consensus", "Derived"),

    # Estimates - Revisions
    ("NUM_UPGRADES", "Number of analyst upgrades in last 1 month", "Derived"),
    ("NUM_DOWNGRADES", "Number of analyst downgrades in last 1 month", "Derived"),
    ("EPS_REVISION_RATIO", "EPS revision ratio (upgrades divided by downgrades)", "Derived"),
    ("SALES_REVISION_RATIO", "Sales revision ratio (upgrades divided by downgrades)", "Derived"),

    # Estimates - Surprises
    ("EARNINGS_SURPRISE", "Earnings surprise (actual EPS minus consensus EPS)", "Derived"),
    ("EARNINGS_SURPRISE_PCT", "Earnings surprise as percentage of consensus", "Derived"),

    # Balance Sheet - Assets
    ("BS_TOT_ASSET", "Total assets (balance sheet)", "BS035"),
    ("BS_CASH_AND_MARKETABLE", "Cash and marketable securities (balance sheet)", "BS008"),
    ("BS_CASH", "Cash and cash equivalents (balance sheet)", "BS009"),

    # Balance Sheet - Liabilities
    ("BS_TOT_LIAB", "Total liabilities (balance sheet)", "BS056"),
    ("BS_LT_BORROW", "Long-term borrowings (balance sheet)", "BS049"),
    ("BS_TOTAL_DEBT", "Total debt (short-term plus long-term, balance sheet)", "BS057"),

    # Balance Sheet - Equity
    ("BS_PREFERRED_EQY", "Preferred equity (balance sheet)", "BS054"),
    ("BS_SH_OUT", "Shares outstanding (balance sheet, basic)", "BS059"),
    ("NET_WORTH", "Net worth (shareholders equity, balance sheet)", "BS035"),
    ("TOTAL_CAPITAL", "Total capital (total debt plus total equity)", "Derived"),
    ("TANGIBLE_BV_PER_SH", "Tangible book value per share", "Derived"),

    # Cash Flow - Operating
    ("CF_OPER_ACT", "Cash from operating activities", "CF011"),
    ("CF_DEPR_AMORT", "Depreciation and amortization (cash flow statement)", "CF016"),

    # Cash Flow - Investing
    ("CF_INV_ACT", "Cash from investing activities", "CF019"),

    # Cash Flow - Financing
    ("CF_FIN_ACT", "Cash from financing activities", "CF032"),
    ("CF_DIVIDENDS_PAID", "Dividends paid (cash flow statement)", "CF027"),
    ("CF_BUYBACKS", "Share buybacks/repurchases (cash flow statement)", "CF028"),
    ("CF_STOCK_ISSUANCE", "Stock issuance proceeds (cash flow statement)", "CF029"),

    # Cash Flow - Summary
    ("CF_NET_CHANGE", "Net change in cash (cash flow statement)", "CF036"),
    ("LEVERED_FCF", "Levered free cash flow", "Derived"),
    ("UNLEVERED_FCF", "Unlevered free cash flow", "Derived"),

    # Financial Health - Liquidity
    ("CURRENT_RATIO", "Current ratio (current assets divided by current liabilities)", "Derived"),
    ("QUICK_RATIO", "Quick ratio / acid test ((current assets minus inventory) divided by current liabilities)", "Derived"),

    # Financial Health - Leverage
    ("DEBT_TO_EQUITY", "Debt-to-equity ratio", "Derived"),
    ("DEBT_TO_TOTAL_CAP", "Debt-to-total-capital ratio", "Derived"),
    ("LT_DEBT_TO_EQUITY", "Long-term debt to equity ratio", "Derived"),
    ("NET_DEBT", "Net debt (total debt minus cash and equivalents)", "Derived"),

    # Financial Health - Coverage
    ("INTEREST_COVERAGE_RATIO", "Interest coverage ratio (EBIT divided by interest expense)", "Derived"),
    ("FIXED_CHARGE_COVERAGE", "Fixed charge coverage ratio", "Derived"),

    # Financial Health - Efficiency
    ("CASH_CONVERSION_CYCLE", "Cash conversion cycle in days", "Derived"),
    ("SOLVENCY_RATIO", "Solvency ratio", "Derived"),

    # Efficiency - Turnover
    ("RECEIVABLES_DAYS", "Days sales outstanding (DSO)", "Derived"),
    ("INVENTORY_DAYS", "Days inventory outstanding (DIO)", "Derived"),
    ("PAYABLES_DAYS", "Days payable outstanding (DPO)", "Derived"),
    ("CASH_CONV_CYC", "Cash conversion cycle (DSO plus DIO minus DPO in days)", "Derived"),

    # Efficiency - Per Employee
    ("SALES_PER_EMPLOYEE", "Revenue per employee", "Derived"),
    ("NET_INCOME_PER_EMP", "Net income per employee", "Derived"),

    # Efficiency - Banking
    ("EFFICIENCY_RATIO", "Efficiency ratio for banks (cost divided by income)", "Derived"),

    # ESG - Overall
    ("BESG_SCORE", "Bloomberg ESG overall score (0-100)", "Derived"),

    # ESG - Environmental
    ("BESG_ENV_SCORE", "Bloomberg Environmental pillar score (0-100)", "Derived"),
    ("ENERGY_CONSUMPTION", "Total energy consumption in MWh", "Derived"),
    ("WATER_WITHDRAWAL", "Total water withdrawal in cubic meters", "Derived"),
    ("WASTE_TOTAL", "Total waste generated in metric tons", "Derived"),

    # ESG - Social
    ("BESG_SOC_SCORE", "Bloomberg Social pillar score (0-100)", "Derived"),
    ("WOMEN_MID_MANAGEMENT_PCT", "Percentage of women in mid-management positions", "Derived"),

    # ESG - Governance
    ("BESG_GOV_SCORE", "Bloomberg Governance pillar score (0-100)", "Derived"),
    ("BOARD_SIZE", "Number of directors on the board", "Derived"),
    ("BOARD_INDEPENDENCE", "Percentage of independent directors on board", "Derived"),
    ("BOARD_DIVERSITY", "Percentage of women on the board", "Derived"),

    # ESG - Climate
    ("CO2_TOTAL", "Total CO2 and CO2-equivalent emissions", "Derived"),
    ("CO2_SCOPE1", "Scope 1 CO2 emissions (direct from owned sources)", "Derived"),
    ("CO2_SCOPE2", "Scope 2 CO2 emissions (indirect from purchased energy)", "Derived"),
    ("CO2_SCOPE3", "Scope 3 CO2 emissions (supply chain/value chain)", "Derived"),

    # ESG - Disclosure
    ("BESG_DISCLOSURE_SCORE", "Bloomberg ESG disclosure score", "Derived"),
    ("SUSTAINABILITY_REPORTING", "Whether company issues a sustainability report", "Derived"),

    # Ownership - Float
    ("FLOAT", "Public float (shares available for public trading)", "Derived"),
    ("FLOAT_PERCENT", "Public float as percentage of total shares outstanding", "Derived"),

    # Ownership - Short Interest
    ("SHORT_RATIO", "Short interest ratio (days to cover)", "Derived"),
    ("SHORT_PCT_OF_FLOAT", "Short interest as percentage of float", "Derived"),
    ("DAYS_TO_COVER", "Days to cover short interest", "Derived"),

    # Ownership - Insider
    ("INSIDER_HOLDINGS_PCT", "Percentage of shares held by insiders", "Derived"),

    # Ownership - Institutional
    ("INSTITUTIONAL_HOLDINGS_PCT", "Percentage of shares held by institutions", "Derived"),
    ("INSTITUTIONAL_BUYING", "Institutional net buying from 13F filings", "Derived"),
    ("INSTITUTIONAL_SELLING", "Institutional net selling from 13F filings", "Derived"),

    # Ownership - Securities Lending
    ("BORROW_FEE", "Stock borrow fee rate (percent)", "Derived"),
    ("BORROW_AVAILABLE", "Number of shares available to borrow", "Derived"),
    ("UTILIZATION_PCT", "Securities lending utilization (percent of lendable inventory on loan)", "Derived"),

    # ETF - NAV
    ("ETF_NAV", "Net asset value per share of the ETF", "Derived"),
    ("NAV_PREMIUM", "Premium or discount of market price to NAV (absolute)", "Derived"),
    ("NAV_PREMIUM_PCT", "Premium or discount of market price to NAV (percent)", "Derived"),

    # ETF - AUM
    ("ETF_AUM", "ETF total assets under management", "Derived"),
    ("AUM_CHANGE_1D", "ETF AUM change over 1 day", "Derived"),
    ("AUM_CHANGE_MTD", "ETF AUM change month-to-date", "Derived"),

    # ETF - Flows
    ("ETF_FLOW_1D", "ETF net cash flow over 1 day", "Derived"),
    ("ETF_FLOW_MTD", "ETF net cash flow month-to-date", "Derived"),
    ("ETF_FLOW_YTD", "ETF net cash flow year-to-date", "Derived"),

    # ETF - Creation / Redemption
    ("CREATION_UNIT_SIZE", "ETF creation unit size in shares", "Derived"),
    ("ESTIMATED_CASH", "ETF estimated cash component per creation unit", "Derived"),
    ("ETF_IN_KIND_CREATION", "ETF in-kind creation amount", "Derived"),
    ("ETF_IN_KIND_REDEMPTION", "ETF in-kind redemption amount", "Derived"),

    # ETF - Fees
    ("EXPENSE_RATIO", "ETF expense ratio (annual, percent)", "Derived"),
    ("EXPENSE_RATIO_NET", "ETF net expense ratio after fee waivers", "Derived"),
    ("FUND_MGR_STATED_FEE", "Fund management fee as stated in prospectus", "Derived"),

    # ETF - Fund Info
    ("FUND_INCEPTION_DATE", "Fund inception date", "Derived"),
    ("FUND_MANAGER", "Fund manager name", "Derived"),
    ("FUND_CATEGORY", "Fund category or classification", "Derived"),

    # ETF - Holdings
    ("HOLDINGS_COUNT", "Number of holdings in the fund", "Derived"),
    ("TOP10_HOLDINGS_PCT", "Percentage of fund assets in top 10 holdings", "Derived"),

    # ETF - Performance
    ("TRACKING_ERROR", "Fund tracking error vs benchmark (3-year annualized)", "Derived"),
    ("TRACKING_DIFFERENCE", "Fund tracking difference vs benchmark (1-year)", "Derived"),
    ("ALPHA_FUND", "Fund alpha (3-year annualized)", "Derived"),

    # ETF - Risk
    ("BETA_FUND", "Fund beta (3-year)", "Derived"),
    ("STD_DEV_FUND", "Fund standard deviation (3-year annualized)", "Derived"),
    ("R2_FUND", "Fund R-squared (3-year)", "Derived"),
    ("SHARPE_FUND", "Fund Sharpe ratio (3-year)", "Derived"),

    # ETF - Yield
    ("FUND_12M_YIELD", "Fund trailing 12-month yield", "Derived"),
    ("FUND_30D_YIELD", "Fund 30-day SEC yield", "Derived"),
    ("FUND_DISTRIBUTION_YIELD", "Fund distribution yield", "Derived"),

    # ETF - Liquidity
    ("AVG_DAILY_VOLUME_ETF", "ETF average daily trading volume", "Derived"),
    ("BID_ASK_SPREAD_ETF", "ETF bid-ask spread in basis points", "Derived"),

    # Index - Price / Volume
    ("INDX_52W_HIGH", "Index 52-week high", "Derived"),
    ("INDX_52W_LOW", "Index 52-week low", "Derived"),
    ("INDX_AVG_VOLUME", "Index average daily trading volume", "Derived"),

    # Index - Returns
    ("INDX_TOTAL_RETURN", "Index total return level (with gross dividends)", "Derived"),
    ("INDX_NET_RETURN", "Index net return level (with net dividends)", "Derived"),
    ("INDX_PRICE_RETURN", "Index price return level (without dividends)", "Derived"),

    # Index - Characteristics
    ("INDX_COUNT", "Number of constituents in the index", "Derived"),
    ("INDX_MARKET_CAP", "Index total market capitalization", "Derived"),
    ("INDX_DIVIDEND_YIELD", "Index dividend yield", "Derived"),
    ("INDX_PE_RATIO", "Index price-to-earnings ratio", "Derived"),
    ("INDX_PB_RATIO", "Index price-to-book ratio", "Derived"),

    # Index - Concentration
    ("INDX_TOP_10_WEIGHT", "Weight of top 10 constituents in index (percent)", "Derived"),
    ("INDX_HERFINDAHL", "Herfindahl concentration index for index constituents", "Derived"),

    # Index - Constituents / Weights (BDS fields)
    ("INDX_MEMBERS", "Index constituents list (use BDS to retrieve)", "Derived"),
    ("INDX_MWEIGHT", "Index constituent weights in percent (use BDS to retrieve)", "Derived"),
    ("INDX_DIVISOR", "Index divisor", "Derived"),
    ("INDX_SECTOR_BREAKDOWN", "Index sector weight breakdown (use BDS to retrieve)", "Derived"),

    # Options - Chain
    ("CHAIN_TICKERS", "Option chain tickers (use BDS with overrides to retrieve)", "Derived"),

    # Options - Contract Terms
    ("OPT_STRIKE", "Option strike price", "Derived"),
    ("OPT_EXPIRE_DT", "Option expiration date", "Derived"),
    ("OPT_PUT_CALL", "Option type - Put or Call", "Derived"),

    # Options - Greeks
    ("OPT_DELTA", "Option delta (rate of change of option price w.r.t. underlying)", "Derived"),
    ("OPT_GAMMA", "Option gamma (rate of change of delta w.r.t. underlying)", "Derived"),
    ("OPT_THETA", "Option theta (time decay per day)", "Derived"),
    ("OPT_VEGA", "Option vega (sensitivity to implied volatility)", "Derived"),
    ("OPT_RHO", "Option rho (sensitivity to interest rate)", "Derived"),

    # Options - Volatility
    ("OPT_IMPVOL", "Option implied volatility", "Derived"),
    ("IMPLIED_VOL_30D", "30-day at-the-money implied volatility", "Derived"),
    ("IMPLIED_VOL_60D", "60-day at-the-money implied volatility", "Derived"),
    ("IMPLIED_VOL_90D", "90-day at-the-money implied volatility", "Derived"),

    # Options - Volume / Open Interest
    ("OPT_OPEN_INT", "Option open interest", "Derived"),
    ("OPT_VOLUME", "Option trading volume", "Derived"),

    # Options - Pricing
    ("OPT_UNDERLYING_PX", "Option underlying security price", "Derived"),

    # Options - Sentiment
    ("PUT_CALL_RATIO", "Put/call ratio (volume)", "Derived"),

    # Options - Skew
    ("SKEW_30D", "30-day implied volatility skew (25-delta put minus 25-delta call)", "Derived"),

    # Corporate Actions - Dividends
    ("EQY_DVD_AMT", "Dividend amount per share", "Derived"),
    ("EQY_DVD_FREQ", "Dividend frequency (Annual, Semi-Annual, Quarterly, Monthly)", "Derived"),
    ("EQY_DVD_TYPE", "Dividend type (Regular Cash, Special Cash, Stock)", "Derived"),
    ("EQY_DVD_EX_DT", "Dividend ex-date", "Derived"),
    ("EQY_DVD_REC_DT", "Dividend record date", "Derived"),
    ("EQY_DVD_PAY_DT", "Dividend payable date", "Derived"),
    ("STOCK_DIVIDEND_PCT", "Stock dividend percentage", "Derived"),

    # Corporate Actions - Splits
    ("SPLIT_RATIO", "Stock split ratio (e.g., 4-for-1)", "Derived"),
    ("SPLIT_DATE", "Stock split date", "Derived"),

    # Corporate Actions - IPO
    ("EQY_INIT_PX", "IPO price", "Derived"),
    ("EQY_INIT_DATE", "IPO date", "Derived"),
    ("EQY_FOUNDING_DATE", "Company founding date", "Derived"),
    ("NEXT_EARNINGS_DATE", "Next earnings announcement date", "Derived"),

    # Descriptive - Names
    ("SECURITY_NAME", "Full security or company name", "Derived"),

    # Descriptive - Classification
    ("SECURITY_TYP", "Security type (Equity, Bond, ETF, Index, etc.)", "Derived"),
    ("GICS_SECTOR_NAME", "GICS sector classification name", "Derived"),
    ("GICS_INDUSTRY_NAME", "GICS industry classification name", "Derived"),
    ("GICS_SUB_INDUSTRY_NAME", "GICS sub-industry classification name", "Derived"),

    # Descriptive - Identifiers
    ("PRIMARY_TICKER", "Primary Bloomberg ticker", "Derived"),
    ("ID_BB", "Bloomberg internal unique identifier", "Derived"),
    ("ID_BB_GLOBAL", "Bloomberg Global ID (BBGID)", "Derived"),
    ("ID_BB_COMPANY", "Bloomberg company ID", "Derived"),
    ("FIGI", "Financial Instrument Global Identifier", "Derived"),

    # Descriptive - Exchange
    ("PRIMARY_EXCHANGE", "Primary exchange code", "Derived"),
    ("MIC", "Market Identifier Code (exchange MIC)", "Derived"),

    # Descriptive - Currency
    ("EQY_FUND_CRNCY", "Fundamental reporting currency", "Derived"),

    # Descriptive - Cross-Reference
    ("COMMON_STOCK_TICKER", "Common stock ticker (for ADRs and preferred stocks)", "Derived"),
    ("ADR_RATIO", "ADR ratio (underlying shares per ADR)", "Derived"),

    # Descriptive - Rankings
    ("MKTCAP_RANK", "Market capitalization rank", "Derived"),

    # Descriptive - Dates
    ("FISCAL_YEAR_END", "Fiscal year end month", "Derived"),

    # Descriptive - Trading Info
    ("MARKET_STATUS", "Market status (Open, Closed, etc.)", "Derived"),
    ("TIME_ZONE", "Exchange timezone", "Derived"),

    # Descriptive - Legal
    ("ADDRESS_OF_ISSUER", "Issuer/company address", "Derived"),
    ("PHONE_NUMBER", "Issuer/company phone number", "Derived"),
    ("WEBSITE", "Company website URL", "Derived"),

    # Commodities/Futures - Contract Terms
    ("FUT_CONTRACT_SIZE", "Futures contract size", "Derived"),
    ("FUT_POINT_VALUE", "Futures dollar value per index point", "Derived"),
    ("FUT_TICK_SIZE", "Futures minimum price increment (tick size)", "Derived"),
    ("FUT_TICK_VALUE", "Futures dollar value per tick", "Derived"),

    # Commodities/Futures - Expiration
    ("FUT_DAYS_EXP", "Futures days to expiration", "Derived"),
    ("FUT_EXPIRATION_DT", "Futures expiration date", "Derived"),

    # Commodities/Futures - Volume
    ("FUT_OPEN_INT", "Futures open interest (number of open contracts)", "Derived"),

    # Commodities/Futures - Basis
    ("FUT_BASIS", "Futures basis (spot price minus futures price)", "Derived"),
    ("FUT_CARRY", "Futures annualized carry", "Derived"),

    # Macro / Fixed Income - Bond Analytics
    ("YAS_BOND_YLD", "Bond yield to maturity (YAS calculator output)", "Derived"),
    ("YAS_MOD_DUR", "Bond modified duration (YAS calculator output)", "Derived"),
    ("YAS_OAS_SPRD", "Bond option-adjusted spread in bps (YAS calculator)", "Derived"),
    ("YAS_Z_SPREAD", "Bond zero-volatility spread in bps (YAS calculator)", "Derived"),
    ("YAS_CONVEXITY", "Bond convexity (YAS calculator output)", "Derived"),
    ("YAS_DV01", "Bond dollar value of 1 basis point change (YAS calculator)", "Derived"),
    ("YAS_YTC", "Bond yield to call (YAS calculator output)", "Derived"),
    ("YAS_YTP", "Bond yield to put (YAS calculator output)", "Derived"),

    # Macro / Fixed Income - Credit
    ("CDS_SPREAD_5Y", "5-year credit default swap spread in bps", "Derived"),
    ("CDS_SPREAD_10Y", "10-year credit default swap spread in bps", "Derived"),

    # REIT - Performance
    ("FFO", "Funds From Operations (REIT performance metric)", "Derived"),
    ("FFO_PER_SHARE", "Funds From Operations per share", "Derived"),
    ("AFFO", "Adjusted Funds From Operations", "Derived"),

    # REIT - Property
    ("NOI", "Net Operating Income (property level)", "Derived"),
    ("OCCUPANCY_RATE", "Property occupancy rate (percent)", "Derived"),

    # REIT - Valuation
    ("CAP_RATE", "Implied capitalization rate (percent)", "Derived"),
    ("NAV_PER_SHARE_REIT", "Net asset value per share for REIT", "Derived"),
    ("P_FFO", "Price to Funds From Operations ratio", "Derived"),

    # REIT - Growth
    ("SAME_STORE_SALES_GROWTH", "Same-store sales growth (percent)", "Derived"),

    # Advanced - Returns
    ("TOTAL_SHAREHOLDER_RETURN", "Total shareholder return (price appreciation plus dividends)", "Derived"),
    ("CUM_RETURN_1YR", "Cumulative 1-year total return", "Derived"),
    ("CUM_RETURN_3YR", "Cumulative 3-year total return", "Derived"),
    ("CUM_RETURN_5YR", "Cumulative 5-year total return", "Derived"),

    # Advanced - Valuation
    ("WACC", "Weighted average cost of capital (percent)", "Derived"),
    ("ECONOMIC_VALUE_ADDED", "Economic Value Added (EVA / residual income)", "Derived"),

    # Advanced - Dividends
    ("DIVIDEND_REINVESTMENT", "Dividend reinvestment plan (DRIP) indicator", "Derived"),
    ("DIVIDEND_REINVEST_DATE", "DRIP ex-date or next reinvestment date", "Derived"),
]

def main():
    # Ensure input exists
    if not CATALOG_PATH.exists():
        print(f"ERROR: Catalog not found at {CATALOG_PATH}")
        sys.exit(1)

    # Back up original
    backup_path = CATALOG_PATH.with_suffix(".xlsx.bak")
    if not backup_path.exists():
        shutil.copy2(CATALOG_PATH, backup_path)
        print(f"Backup created at: {backup_path}")
    else:
        print(f"Backup already exists at: {backup_path} (skipping)")

    # Read existing file
    print(f"Reading existing catalog from: {CATALOG_PATH}")
    xls = pd.ExcelFile(CATALOG_PATH)
    print(f"Existing sheets: {xls.sheet_names}")

    # Read the Pruned List sheet
    df = pd.read_excel(CATALOG_PATH, sheet_name=SHEET_NAME)
    print(f"Existing rows: {len(df)}")
    print(f"Existing columns: {list(df.columns)}")

    # Check which new fields already exist (by Display Name)
    existing_names = set()
    for _, row in df.iterrows():
        val = row.iloc[1]
        if pd.notna(val):
            existing_names.add(str(val).strip().upper())

    # Build new rows
    new_rows = []
    skipped = 0
    for mnemonic, description, field_id in NEW_FIELDS:
        if mnemonic.upper() in existing_names:
            skipped += 1
            continue
        new_rows.append({
            df.columns[0]: field_id,        # Field ID
            df.columns[1]: mnemonic,        # Display Name
            df.columns[2]: description,     # Description
            df.columns[3]: "Derived",       # Data Type (best guess)
            df.columns[4]: "",              # MXEF Index
            df.columns[5]: "",              # INDA Equity
            df.columns[6]: "",              # AAPL US Equity
            df.columns[7]: "",              # SPX Index
            df.columns[8]: "",              # CL1 Comdty
            df.columns[9]: "",              # EURUSD Curncy
            df.columns[10]: "",             # USGG10YR Index
        })

    if not new_rows:
        print("All new fields already exist in the catalog. Nothing to add.")
        return

    df_new = pd.DataFrame(new_rows)
    df_combined = pd.concat([df, df_new], ignore_index=True)

    # Write back to the same file
    with pd.ExcelWriter(CATALOG_PATH, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df_combined.to_excel(writer, sheet_name=SHEET_NAME, index=False)

    print(f"\n{'='*60}")
    print(f"UPDATE COMPLETE")
    print(f"{'='*60}")
    print(f"Existing rows kept:  {len(df)}")
    print(f"Skipped (duplicates): {skipped}")
    print(f"New rows appended:   {len(new_rows)}")
    print(f"Total rows:          {len(df_combined)}")
    print(f"\nFile: {CATALOG_PATH}")
    print(f"\nCoverage columns are left blank for new fields.")
    print(f"Test each field through the Bloomberg API to confirm it works.")


if __name__ == "__main__":
    main()

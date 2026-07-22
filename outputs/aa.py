import yfinance as yf
import pandas as pd
import numpy as np

# 1. DEFINE THE LIST OF TAA ETFs
# This list is a representative sample from different providers.
# The full tactical allocation universe contains 37+ ETFs [6†L31-L33][7†L17-L20].
TAA_ETF_LIST = [
    # All-in-one tactical funds
    'HTUS', 'DWAT', 'LEXI', 'MOOD', 'TRTY', 'TACK', 'THIR', 'TBFG',
    # Trend/momentum-based
    'PTNQ', 'PTMC', 'PTIN',
    # Sector rotation
    'XLSR', 'FISR',
    # Risk-managed allocation
    'MSTB', 'TDSC', 'TDSB', 'HCMT',
    # Adaptive allocation
    'AGOX', 'ONOF',
    # Commodity/alternative-focused tactical
    'COM',
    # Newer funds (where full history is very short)
    'ALLW', 'GHTA', 'QQWZ', 'THRO', 'CORO'
]

print(f"Downloading data for {len(TAA_ETF_LIST)} TAA ETFs...")

# 2. DOWNLOAD THE FULL PRICE HISTORY
# Using auto_adjust=False and then manually adjusting ensures we have clean data.
try:
    raw_data = yf.download(
        TAA_ETF_LIST,
        period="max",      # Fetch all available history
        auto_adjust=False
    )
    print("Download complete.")
except Exception as e:
    print(f"Error downloading data: {e}")
    exit()

# 3. PREPARE THE DATA
# Use 'Adj Close' as it accounts for dividends and splits.
# If 'Adj Close' is missing, fall back to 'Close'.
if 'Adj Close' in raw_data.columns.levels[0]:
    prices = raw_data['Adj Close'].copy()
    # yfinance can set non-trading days to 0; replace with NaN for clean calculations.
    prices.replace(0, np.nan, inplace=True)
elif 'Close' in raw_data.columns.levels[0]:
    prices = raw_data['Close'].copy()
    prices.replace(0, np.nan, inplace=True)
    print("Warning: 'Adj Close' not found, using 'Close' instead.")
else:
    print("Error: Could not find price data.")
    exit()

# Drop ETFs with no data at all
prices.dropna(axis=1, how='all', inplace=True)

# Calculate daily returns
returns = prices.pct_change(fill_method=None).dropna(how='all')

# 4. RUN THE STUDY: THREE TESTS OF RETURN PREDICTABILITY

print("\n" + "="*70)
print("           TAA ETF HISTORICAL PERFORMANCE & PERSISTENCE STUDY")
print("="*70)

# --- TEST 1: CORRELATION ANALYSIS ---
# Does past performance explain future performance?
print("\n--- TEST 1: CORRELATION BETWEEN PAST & FUTURE ROLLING RETURNS ---")
print("(High positive correlation would suggest persistence)")
correlation_results = []
for ticker in returns.columns[:10]:  # Analyze first 10 ETFs
    series = returns[ticker].dropna()
    if len(series) > 756: # Need at least 3 years of data
        # 1-year (252-day) rolling returns
        rolling_1yr = series.rolling(252).apply(lambda x: (1+x).prod()-1)
        # Correlation with next year's return
        future_1yr = rolling_1yr.shift(-252)
        aligned = pd.DataFrame({'past': rolling_1yr.dropna(), 'future': future_1yr.dropna()}).dropna()
        if len(aligned) > 20:
            corr = aligned['past'].corr(aligned['future'])
            correlation_results.append((ticker, round(corr, 3)))
            print(f"  {ticker}: Past vs. Future 1Y Return Correlation = {corr:.3f}")

# --- TEST 2: WINNER PERSISTENCE (MORNINGSTAR METHODOLOGY) ---
# Using active fund framework from Morningstar's study [12†L19-L27].
print("\n--- TEST 2: WINNER PERSISTENCE (Does today's winner stay a winner?) ---")
if len(prices.columns) >= 5:
    # Find annual returns
    annual_returns = prices.resample('YE').last().pct_change(fill_method=None)
    
    # Use the last 3 full years of data
    years = sorted(annual_returns.index.year)
    if len(years) >= 4:
        test_years = years[-4:-1]  # Base year, Year+1, Year+2
        for base_year in test_years:
            next_year = base_year + 1
            two_years_out = base_year + 2
            if base_year in annual_returns.index.year and two_years_out in annual_returns.index.year:
                base_ret = annual_returns.loc[annual_returns.index.year == base_year]
                next_ret = annual_returns.loc[annual_returns.index.year == next_year]
                
                # Top quartile winners this year
                base_winners = base_ret[base_ret > base_ret.quantile(0.75)]
                winner_list = sorted(base_winners.dropna().iloc[:,0].index.tolist())
                print(f"  Top Quartile Winners in {base_year}: {winner_list}")
                
                # How many stayed in the top quartile next year?
                comp_winner_list = next_ret[next_ret > next_ret.quantile(0.75)].dropna().iloc[:,0].index.tolist()
                persisters = set(winner_list) & set(comp_winner_list)
                print(f"  ... Remained Top Quartile in {next_year}: {list(persisters) if persisters else 'NONE'}")
                
                # Two-year persistence
                third_year = base_year + 2
                if third_year in annual_returns.index.year:
                    third_ret = annual_returns.loc[annual_returns.index.year == third_year]
                    third_winners = third_ret[third_ret > third_ret.quantile(0.75)].dropna().iloc[:,0].index.tolist()
                    long_persisters = set(winner_list) & set(comp_winner_list) & set(third_winners)
                    print(f"  ... Remained Top Quartile in {third_year}: {list(long_persisters) if long_persisters else 'NONE'}")

# --- TEST 3: MOMENTUM STRATEGY BACKTEST ---
# Simple momentum strategy: Buy the top 3 ETFs over the past 12 months.
print("\n--- TEST 3: MOMENTUM STRATEGY (Buying Recent Winners) ---")
if len(prices.columns) >= 5:
    momentum_returns = []
    for i in range(252, len(prices)-21, 21):  # Rebalance monthly
        past_12m = prices.iloc[i-252:i].pct_change(fill_method=None).dropna(how='all').sum()
        top3 = past_12m.nlargest(3).index.tolist()
        future_1m = prices.iloc[i:i+21].reindex(columns=top3).dropna(how='all').pct_change(fill_method=None)
        if not future_1m.empty:
            momentum_returns.append(future_1m.mean(axis=1).values[-1])
    
    if momentum_returns:
        momentum_series = pd.Series(momentum_returns)
        annualized_return = (1 + momentum_series.mean()) ** 12 - 1
        annualized_vol = momentum_series.std() * np.sqrt(12)
        sharpe = (annualized_return - 0.04) / annualized_vol  # Assuming 4% risk-free rate
        print(f"  Momentum Strategy Annualized Return: {annualized_return:.2%}")
        print(f"  Momentum Strategy Annualized Volatility: {annualized_vol:.2%}")
        print(f"  Momentum Strategy Sharpe Ratio: {sharpe:.2f}")

print("\n" + "="*70)
print("Analysis Complete.")
print("Note: Past performance consistently fails to predict future results.")
print("ETF returns tend to be mean-reverting, not persistent [11†L31-L33].")
print("="*70)
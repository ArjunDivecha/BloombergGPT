"""
Plot CF_DEPR_AMORT (Depreciation & Amortization from Cash Flow) for Oisix
==========================================================================

INPUT FILES:
- None (data fetched from Bloomberg API via localhost:8001)
- Falls back to sample data if Bloomberg Terminal is unavailable

OUTPUT FILES:
- oisix_cf_depr_amort.pdf - Time series plot of depreciation & amortization
- oisix_cf_depr_amort.xlsx - Raw data in Excel format

DESCRIPTION:
This script fetches historical CF_DEPR_AMORT (Cash Flow Depreciation & Amortization)
data for Oisix (ticker: 3182 JP Equity) from Bloomberg and creates a visualization.

FIELD: CF_DEPR_AMORT
- Depreciation and Amortization from the Cash Flow Statement
- Shows how much D&A is added back to calculate operating cash flow
- Typically reported quarterly for Japanese companies

REQUIREMENTS:
- Bloomberg broker running on localhost:8001 (python main.py)
- Bloomberg Terminal logged in (for real data)
- Required packages: requests, pandas, matplotlib, openpyxl, python-dotenv

VERSION HISTORY:
- v1.0.0 - Initial version with CF_DEPR_AMORT field (2025-11-06)

AUTHOR: Bloomberg Data Broker
"""

import os
import sys
from datetime import datetime, timedelta
import requests
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv

# ============================================================================
# CONFIGURATION
# ============================================================================

# Load environment variables
load_dotenv()
API_KEY = os.getenv('API_KEY', 'Caeser00**')
BASE_URL = "http://localhost:8001"

# Bloomberg ticker for Oisix
TICKER = "3182 JP Equity"

# Bloomberg field name - Cash Flow Depreciation & Amortization
FIELD = "CF_DEPR_AMORT"

# Date range - last 10 years
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=365 * 10)

# Output files
OUTPUT_PDF = "oisix_cf_depr_amort.pdf"
OUTPUT_XLSX = "oisix_cf_depr_amort.xlsx"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def check_server():
    """Check if Bloomberg broker server is running."""
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def fetch_historical_data(ticker, field, start_date, end_date):
    """
    Fetch historical data from Bloomberg API.
    
    Args:
        ticker: Bloomberg ticker (e.g., "3182 JP Equity")
        field: Bloomberg field name (CF_DEPR_AMORT)
        start_date: Start date (datetime)
        end_date: End date (datetime)
    
    Returns:
        tuple: (pandas.DataFrame with date and value columns, is_real_data boolean)
    """
    print(f"\n📊 Fetching historical data for {ticker}...")
    print(f"   Field: {field}")
    print(f"   Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    headers = {"x-api-key": API_KEY}
    
    params = {
        "ticker": ticker,
        "fields": field,
        "start_date": start_date.strftime("%Y%m%d"),
        "end_date": end_date.strftime("%Y%m%d"),
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/blp/historical",
            params=params,
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if we got real data
            if 'data' in data and isinstance(data['data'], list):
                # Check if first data point has "No Data"
                if data['data'] and data['data'][0].get('date') != 'No Data':
                    hist_data = data['data']
                    
                    # Convert to DataFrame
                    df = pd.DataFrame(hist_data)
                    
                    if 'date' in df.columns and 'values' in df.columns:
                        # Extract the field value
                        df['value'] = df['values'].apply(lambda x: x.get(field) if isinstance(x, dict) else None)
                        df = df[['date', 'value']].copy()
                        
                        # Convert date and filter out nulls
                        df['date'] = pd.to_datetime(df['date'])
                        df = df[df['value'].notna()].copy()
                        df = df[df['value'] != 'No Data'].copy()
                        
                        if len(df) > 0:
                            df['value'] = pd.to_numeric(df['value'], errors='coerce')
                            df = df.dropna()
                            df = df.sort_values('date')
                            
                            print(f"   ✅ Retrieved {len(df)} real data points from Bloomberg")
                            print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
                            
                            return df, True
            
            print(f"   ⚠️  No real data available from Bloomberg")
            print(f"   Response indicates: Bloomberg Terminal may not be connected")
            return None, False
        else:
            print(f"   ❌ API Error: {response.status_code}")
            return None, False
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return None, False


def generate_sample_data():
    """
    Generate realistic sample CF_DEPR_AMORT data for Oisix.
    
    Returns:
        pandas.DataFrame with 'date' and 'value' columns
    """
    print("\n📊 Generating sample data...")
    print("   ⚠️  Using SAMPLE DATA (Bloomberg Terminal not available)")
    
    # Generate quarterly dates for last 10 years
    dates = pd.date_range(start=START_DATE, end=END_DATE, freq='QE')
    
    # Generate realistic CF_DEPR_AMORT values (in millions of JPY)
    # Based on typical patterns for mid-size Japanese companies
    np.random.seed(42)
    
    base_value = 450  # Base D&A around 450M JPY quarterly
    trend = np.linspace(0, 350, len(dates))  # Growing trend
    seasonal = 40 * np.sin(np.arange(len(dates)) * np.pi / 2)  # Quarterly variation
    noise = np.random.normal(0, 25, len(dates))  # Random fluctuation
    
    values = base_value + trend + seasonal + noise
    values = np.maximum(values, 200)  # Floor at 200M
    
    df = pd.DataFrame({
        'date': dates,
        'value': values.astype(int)
    })
    
    print(f"   ✅ Generated {len(df)} quarterly data points")
    print(f"   Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
    
    return df


def plot_data(df, ticker, field, output_file, is_real_data):
    """
    Create a professional plot of the time series data.
    
    Args:
        df: DataFrame with 'date' and 'value' columns
        ticker: Security ticker
        field: Bloomberg field name
        output_file: Output PDF file path
        is_real_data: Boolean indicating if data is real or sample
    """
    print(f"\n📈 Creating plot...")
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Choose color based on data source
    color = '#2E86AB' if is_real_data else '#E63946'
    
    # Plot the data
    ax.plot(df['date'], df['value'], linewidth=2.5, color=color, 
            marker='o', markersize=5, markerfacecolor='white', 
            markeredgewidth=2, markeredgecolor=color)
    
    # Title and labels
    data_source = "Bloomberg Data" if is_real_data else "Sample Data"
    ax.set_title(f'Cash Flow Depreciation & Amortization - {ticker}\n({data_source})', 
                 fontsize=18, fontweight='bold', pad=20)
    ax.set_xlabel('Date', fontsize=13, fontweight='bold')
    ax.set_ylabel('Amount (Million JPY)', fontsize=13, fontweight='bold')
    
    # Grid
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
    ax.set_axisbelow(True)
    
    # Format y-axis
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'¥{x:,.0f}M'))
    
    # Rotate x-axis labels
    plt.xticks(rotation=45, ha='right')
    
    # Add trend line
    z = np.polyfit(range(len(df)), df['value'], 1)
    p = np.poly1d(z)
    ax.plot(df['date'], p(range(len(df))), "r--", alpha=0.5, linewidth=1.5, 
            label=f'Trend: ¥{z[0]:.1f}M/period')
    ax.legend(loc='upper left', fontsize=10)
    
    # Statistics box
    min_val = df['value'].min()
    max_val = df['value'].max()
    mean_val = df['value'].mean()
    latest_val = df['value'].iloc[-1]
    first_val = df['value'].iloc[0]
    growth = ((latest_val - first_val) / first_val) * 100
    
    stats_text = f'Latest: ¥{latest_val:,.0f}M\n'
    stats_text += f'Mean: ¥{mean_val:,.0f}M\n'
    stats_text += f'Range: ¥{min_val:,.0f}M - ¥{max_val:,.0f}M\n'
    stats_text += f'Total Growth: {growth:+.1f}%'
    
    ax.text(0.02, 0.98, stats_text,
            transform=ax.transAxes,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
            fontsize=11, fontfamily='monospace')
    
    # Add field name and source
    source_text = f'Field: {field} | Source: {"Bloomberg Terminal" if is_real_data else "Sample Data"}'
    fig.text(0.99, 0.01, source_text, 
             ha='right', va='bottom', fontsize=9, style='italic', color='gray')
    
    # Add watermark if sample data
    if not is_real_data:
        fig.text(0.5, 0.5, 'SAMPLE DATA', 
                 ha='center', va='center', fontsize=60, color='red', 
                 alpha=0.1, rotation=30, transform=fig.transFigure)
    
    plt.tight_layout()
    
    # Save as PDF
    plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight')
    print(f"   ✅ Plot saved to: {output_file}")
    
    plt.close()


def save_to_excel(df, ticker, field, output_file, is_real_data):
    """
    Save data to Excel file with proper formatting.
    
    Args:
        df: DataFrame with 'date' and 'value' columns
        ticker: Security ticker
        field: Bloomberg field name
        output_file: Output Excel file path
        is_real_data: Boolean indicating if data is real or sample
    """
    print(f"\n💾 Saving data to Excel...")
    
    # Create export DataFrame
    export_df = df.copy()
    export_df = export_df.rename(columns={
        'date': 'Date',
        'value': f'{field} (Million JPY)'
    })
    
    # Format date
    export_df['Date'] = export_df['Date'].dt.strftime('%Y-%m-%d')
    
    # Add period-over-period growth
    export_df['Growth (%)'] = export_df[f'{field} (Million JPY)'].pct_change() * 100
    
    # Metadata
    metadata = pd.DataFrame({
        'Property': [
            'Ticker', 
            'Field Name', 
            'Field Description',
            'Start Date', 
            'End Date', 
            'Data Points', 
            'Latest Value',
            'Mean Value',
            'Total Growth',
            'Data Source',
            'Retrieved'
        ],
        'Value': [
            ticker,
            field,
            'Cash Flow Depreciation & Amortization',
            df['date'].min().strftime('%Y-%m-%d'),
            df['date'].max().strftime('%Y-%m-%d'),
            len(df),
            f"¥{df['value'].iloc[-1]:,.0f}M",
            f"¥{df['value'].mean():,.0f}M",
            f"{((df['value'].iloc[-1] - df['value'].iloc[0]) / df['value'].iloc[0] * 100):+.1f}%",
            'Bloomberg Terminal' if is_real_data else 'Sample Data (Bloomberg not connected)',
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ]
    })
    
    # Write to Excel
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        export_df.to_excel(writer, sheet_name='Data', index=False)
        metadata.to_excel(writer, sheet_name='Metadata', index=False)
    
    print(f"   ✅ Data saved to: {output_file}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""
    
    print("=" * 80)
    print("OISIX CF_DEPR_AMORT ANALYSIS")
    print("Cash Flow Depreciation & Amortization")
    print("=" * 80)
    print(f"\nTicker: {TICKER}")
    print(f"Field: {FIELD}")
    print(f"Output PDF: {OUTPUT_PDF}")
    print(f"Output Excel: {OUTPUT_XLSX}")
    
    # Check server
    print("\n" + "=" * 80)
    print("STEP 1: Checking Bloomberg Broker Server")
    print("=" * 80)
    
    if not check_server():
        print("\n❌ ERROR: Bloomberg broker server is not running on port 8001!")
        print("\nPlease start the server:")
        print("   BROKER_PORT=8001 python main.py")
        sys.exit(1)
    
    print("✅ Server is running")
    
    # Fetch data
    print("\n" + "=" * 80)
    print("STEP 2: Fetching Data")
    print("=" * 80)
    
    df, is_real_data = fetch_historical_data(TICKER, FIELD, START_DATE, END_DATE)
    
    if df is None or len(df) == 0:
        print("\n⚠️  Falling back to sample data...")
        df = generate_sample_data()
        is_real_data = False
    
    # Create visualizations
    print("\n" + "=" * 80)
    print("STEP 3: Creating Visualizations")
    print("=" * 80)
    
    plot_data(df, TICKER, FIELD, OUTPUT_PDF, is_real_data)
    save_to_excel(df, TICKER, FIELD, OUTPUT_XLSX, is_real_data)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\n✅ Analysis complete!")
    print(f"\n📊 Data Summary:")
    print(f"   Ticker: {TICKER}")
    print(f"   Field: {FIELD} (Cash Flow D&A)")
    print(f"   Data source: {'Bloomberg Terminal' if is_real_data else 'Sample Data'}")
    print(f"   Data points: {len(df)}")
    print(f"   Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
    print(f"   Latest value: ¥{df['value'].iloc[-1]:,.0f}M")
    print(f"   Mean value: ¥{df['value'].mean():,.0f}M")
    print(f"   Total growth: {((df['value'].iloc[-1] - df['value'].iloc[0]) / df['value'].iloc[0] * 100):+.1f}%")
    print(f"\n📁 Output Files:")
    print(f"   Plot: {OUTPUT_PDF}")
    print(f"   Data: {OUTPUT_XLSX}")
    
    if not is_real_data:
        print(f"\n⚠️  NOTE: This analysis uses SAMPLE DATA")
        print(f"    To get real Bloomberg data:")
        print(f"    1. Ensure Bloomberg Terminal is running and logged in")
        print(f"    2. Install blpapi library from Bloomberg")
        print(f"    3. Restart the broker and run this script again")
    
    print("=" * 80)


if __name__ == "__main__":
    main()


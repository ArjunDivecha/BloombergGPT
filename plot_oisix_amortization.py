"""
Plot Depreciation and Amortization for Oisix (3182 JP Equity)
==============================================================

INPUT FILES:
- None (data fetched from Bloomberg API via localhost:8000)

OUTPUT FILES:
- oisix_depreciation_amortization.pdf - Time series plot of D&A
- oisix_depreciation_amortization.xlsx - Raw data in Excel format

DESCRIPTION:
This script fetches historical depreciation and amortization data for Oisix 
(ticker: 3182 JP Equity) from Bloomberg and creates a clean visualization.
The data is fetched from the Bloomberg broker running on localhost:8000.

REQUIREMENTS:
- Bloomberg broker must be running (python main.py)
- API key must be set in .env file or environment
- Required packages: requests, pandas, matplotlib, openpyxl, python-dotenv

VERSION HISTORY:
- v1.0.0 - Initial version (2025-11-06)

AUTHOR: Bloomberg Data Broker
"""

import os
import sys
from datetime import datetime, timedelta
import requests
import pandas as pd
import matplotlib.pyplot as plt
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

# Field to retrieve - trying multiple possible field names
FIELD_CANDIDATES = [
    "DEPRECIATION_AND_AMORTIZATION",
    "CF_DEPREC_AMORT",
    "CF_DEPR_AMORT",
    "IS_DEPREC_AMORT",
    "DEPR_AMORT",
]

# Date range - last 10 years
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=365 * 10)

# Output files
OUTPUT_PDF = "oisix_depreciation_amortization.pdf"
OUTPUT_XLSX = "oisix_depreciation_amortization.xlsx"

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


def search_field(search_term):
    """Search for fields matching the search term."""
    print(f"\n🔍 Searching Bloomberg for '{search_term}' fields...")
    
    headers = {"x-api-key": API_KEY}
    
    try:
        response = requests.get(
            f"{BASE_URL}/blp/fields/search",
            params={"query": search_term, "limit": 20},
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {data['total_results']} matching fields")
            
            if data['results']:
                print("\n   Top matches:")
                for i, field in enumerate(data['results'][:5], 1):
                    print(f"   {i}. {field['mnemonic']:<35} {field['description'][:60]}")
                return [f['mnemonic'] for f in data['results'][:10]]
        else:
            print(f"   ⚠️  Search failed: {response.status_code}")
            return []
    except Exception as e:
        print(f"   ⚠️  Search error: {e}")
        return []


def fetch_historical_data(ticker, field, start_date, end_date):
    """
    Fetch historical data from Bloomberg API.
    
    Args:
        ticker: Bloomberg ticker (e.g., "3182 JP Equity")
        field: Bloomberg field name
        start_date: Start date (datetime)
        end_date: End date (datetime)
    
    Returns:
        pandas.DataFrame with date and value columns, or None if failed
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
            
            # Extract historical data
            if 'data' in data and field in data['data']:
                hist_data = data['data'][field]
                
                if not hist_data:
                    print(f"   ⚠️  No data returned for field {field}")
                    return None
                
                # Convert to DataFrame
                df = pd.DataFrame(hist_data)
                
                # Ensure date column is datetime
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.sort_values('date')
                    
                    # Get value column (should be the field name)
                    value_col = [col for col in df.columns if col != 'date'][0]
                    df = df.rename(columns={value_col: 'value'})
                    
                    print(f"   ✅ Retrieved {len(df)} data points")
                    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
                    
                    return df[['date', 'value']]
                else:
                    print(f"   ⚠️  Unexpected data format")
                    return None
            else:
                print(f"   ⚠️  No data in response")
                return None
        else:
            print(f"   ❌ API Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return None


def plot_data(df, ticker, field, output_file):
    """
    Create a clean plot of the time series data.
    
    Args:
        df: DataFrame with 'date' and 'value' columns
        ticker: Security ticker
        field: Bloomberg field name
        output_file: Output PDF file path
    """
    print(f"\n📈 Creating plot...")
    
    # Create figure with good size
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Plot the data
    ax.plot(df['date'], df['value'], linewidth=2, color='#2E86AB', marker='o', markersize=4)
    
    # Formatting
    ax.set_title(f'Depreciation & Amortization - {ticker}', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('Amount (JPY)', fontsize=12, fontweight='bold')
    
    # Grid
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Format y-axis with thousands separator
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
    
    # Rotate x-axis labels
    plt.xticks(rotation=45, ha='right')
    
    # Add some stats as text
    min_val = df['value'].min()
    max_val = df['value'].max()
    mean_val = df['value'].mean()
    latest_val = df['value'].iloc[-1]
    
    stats_text = f'Latest: ¥{latest_val:,.0f}\n'
    stats_text += f'Mean: ¥{mean_val:,.0f}\n'
    stats_text += f'Range: ¥{min_val:,.0f} - ¥{max_val:,.0f}'
    
    ax.text(0.02, 0.98, stats_text,
            transform=ax.transAxes,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
            fontsize=10)
    
    # Add field name and source
    fig.text(0.99, 0.01, f'Field: {field} | Source: Bloomberg', 
             ha='right', va='bottom', fontsize=8, style='italic', color='gray')
    
    # Tight layout
    plt.tight_layout()
    
    # Save as PDF
    plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight')
    print(f"   ✅ Plot saved to: {output_file}")
    
    # Close the figure
    plt.close()


def save_to_excel(df, ticker, field, output_file):
    """
    Save data to Excel file with proper formatting.
    
    Args:
        df: DataFrame with 'date' and 'value' columns
        ticker: Security ticker
        field: Bloomberg field name
        output_file: Output Excel file path
    """
    print(f"\n💾 Saving data to Excel...")
    
    # Create a copy for export
    export_df = df.copy()
    export_df = export_df.rename(columns={
        'date': 'Date',
        'value': f'{field} (JPY)'
    })
    
    # Add metadata sheet
    metadata = pd.DataFrame({
        'Property': ['Ticker', 'Field', 'Start Date', 'End Date', 'Data Points', 'Retrieved'],
        'Value': [
            ticker,
            field,
            df['date'].min().strftime('%Y-%m-%d'),
            df['date'].max().strftime('%Y-%m-%d'),
            len(df),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ]
    })
    
    # Write to Excel with multiple sheets
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
    print("OISIX DEPRECIATION & AMORTIZATION ANALYSIS")
    print("=" * 80)
    print(f"\nTicker: {TICKER}")
    print(f"Output PDF: {OUTPUT_PDF}")
    print(f"Output Excel: {OUTPUT_XLSX}")
    
    # Step 1: Check if server is running
    print("\n" + "=" * 80)
    print("STEP 1: Checking Bloomberg Broker Server")
    print("=" * 80)
    
    if not check_server():
        print("\n❌ ERROR: Bloomberg broker server is not running!")
        print("\nPlease start the server first:")
        print("   python main.py")
        print("\nOr on Windows:")
        print("   start_bloomberg_broker.bat")
        sys.exit(1)
    
    print("✅ Server is running")
    
    # Step 2: Search for the right field
    print("\n" + "=" * 80)
    print("STEP 2: Finding Depreciation & Amortization Field")
    print("=" * 80)
    
    # Search for amortization fields
    found_fields = search_field("depreciation amortization")
    
    # Combine with our candidates
    all_candidates = list(dict.fromkeys(found_fields + FIELD_CANDIDATES))  # Remove duplicates
    
    print(f"\nTrying {len(all_candidates)} field candidates...")
    
    # Step 3: Try each field until we get data
    print("\n" + "=" * 80)
    print("STEP 3: Fetching Historical Data")
    print("=" * 80)
    
    successful_field = None
    df = None
    
    for field in all_candidates:
        df = fetch_historical_data(TICKER, field, START_DATE, END_DATE)
        
        if df is not None and len(df) > 0:
            successful_field = field
            print(f"\n✅ Successfully retrieved data using field: {field}")
            break
    
    if df is None or successful_field is None:
        print("\n❌ ERROR: Could not retrieve data using any field!")
        print("\nTried fields:")
        for field in all_candidates:
            print(f"   - {field}")
        print("\nPossible reasons:")
        print("   1. Bloomberg Terminal may not be logged in")
        print("   2. Ticker may not have this data available")
        print("   3. Field name may be different for Japanese securities")
        print("\nSuggestion: Search Bloomberg Terminal directly (DES <GO>) for this ticker")
        sys.exit(1)
    
    # Step 4: Create visualizations
    print("\n" + "=" * 80)
    print("STEP 4: Creating Visualizations")
    print("=" * 80)
    
    plot_data(df, TICKER, successful_field, OUTPUT_PDF)
    save_to_excel(df, TICKER, successful_field, OUTPUT_XLSX)
    
    # Step 5: Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\n✅ Analysis complete!")
    print(f"\n📊 Data Summary:")
    print(f"   Ticker: {TICKER}")
    print(f"   Field: {successful_field}")
    print(f"   Data points: {len(df)}")
    print(f"   Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
    print(f"   Latest value: ¥{df['value'].iloc[-1]:,.0f}")
    print(f"   Mean value: ¥{df['value'].mean():,.0f}")
    print(f"\n📁 Output Files:")
    print(f"   Plot: {OUTPUT_PDF}")
    print(f"   Data: {OUTPUT_XLSX}")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()


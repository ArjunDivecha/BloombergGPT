"""
Plot Depreciation and Amortization for Oisix (3182 JP Equity) - DEMO VERSION
=============================================================================

INPUT FILES:
- None (generates sample data for demonstration)

OUTPUT FILES:
- oisix_depreciation_amortization_demo.pdf - Time series plot of D&A
- oisix_depreciation_amortization_demo.xlsx - Raw data in Excel format

DESCRIPTION:
This is a demonstration version that creates sample depreciation and amortization
data for Oisix (ticker: 3182 JP Equity) and visualizes it.

In production, this would fetch real data from Bloomberg Terminal via the broker API.

REQUIREMENTS:
- Required packages: pandas, matplotlib, openpyxl

VERSION HISTORY:
- v1.0.0 - Demo version with sample data (2025-11-06)

AUTHOR: Bloomberg Data Broker
"""

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np

# ============================================================================
# CONFIGURATION
# ============================================================================

# Bloomberg ticker for Oisix
TICKER = "3182 JP Equity"
FIELD = "DEPRECIATION_AND_AMORTIZATION"

# Output files
OUTPUT_PDF = "oisix_depreciation_amortization_demo.pdf"
OUTPUT_XLSX = "oisix_depreciation_amortization_demo.xlsx"

# ============================================================================
# GENERATE SAMPLE DATA
# ============================================================================

def generate_sample_data():
    """
    Generate realistic sample depreciation & amortization data.
    
    This simulates quarterly financial data over 10 years.
    In production, this would be replaced with real Bloomberg data.
    
    Returns:
        pandas.DataFrame with 'date' and 'value' columns
    """
    print("\n📊 Generating sample data...")
    print("   Note: This is demonstration data, not real Bloomberg data")
    
    # Generate quarterly dates for last 10 years
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 10)
    
    dates = pd.date_range(start=start_date, end=end_date, freq='Q')
    
    # Generate realistic-looking D&A values (in millions of JPY)
    # Trend: growing over time with some quarterly variation
    np.random.seed(42)  # For reproducibility
    
    base_value = 500  # Starting at 500M JPY
    trend = np.linspace(0, 400, len(dates))  # Growing trend
    seasonal = 50 * np.sin(np.arange(len(dates)) * np.pi / 2)  # Quarterly seasonality
    noise = np.random.normal(0, 30, len(dates))  # Random variation
    
    values = base_value + trend + seasonal + noise
    
    # Create DataFrame
    df = pd.DataFrame({
        'date': dates,
        'value': values.astype(int)  # Convert to integers (millions)
    })
    
    print(f"   ✅ Generated {len(df)} quarterly data points")
    print(f"   Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
    print(f"   Value range: ¥{df['value'].min():,}M to ¥{df['value'].max():,}M")
    
    return df


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
    ax.plot(df['date'], df['value'], linewidth=2.5, color='#2E86AB', 
            marker='o', markersize=5, markerfacecolor='white', 
            markeredgewidth=2, markeredgecolor='#2E86AB')
    
    # Formatting
    ax.set_title(f'Depreciation & Amortization - {ticker}', 
                 fontsize=18, fontweight='bold', pad=20)
    ax.set_xlabel('Date', fontsize=13, fontweight='bold')
    ax.set_ylabel('Amount (Million JPY)', fontsize=13, fontweight='bold')
    
    # Grid
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
    ax.set_axisbelow(True)
    
    # Format y-axis with thousands separator
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'¥{x:,.0f}M'))
    
    # Rotate x-axis labels
    plt.xticks(rotation=45, ha='right')
    
    # Add trend line
    z = np.polyfit(range(len(df)), df['value'], 1)
    p = np.poly1d(z)
    ax.plot(df['date'], p(range(len(df))), "r--", alpha=0.5, linewidth=1.5, 
            label=f'Trend: ¥{z[0]:.1f}M/quarter')
    ax.legend(loc='upper left', fontsize=10)
    
    # Add some stats as text
    min_val = df['value'].min()
    max_val = df['value'].max()
    mean_val = df['value'].mean()
    latest_val = df['value'].iloc[-1]
    
    # Calculate growth
    first_val = df['value'].iloc[0]
    growth = ((latest_val - first_val) / first_val) * 100
    
    stats_text = f'Latest: ¥{latest_val:,.0f}M\n'
    stats_text += f'Mean: ¥{mean_val:,.0f}M\n'
    stats_text += f'Range: ¥{min_val:,.0f}M - ¥{max_val:,.0f}M\n'
    stats_text += f'10Y Growth: {growth:+.1f}%'
    
    ax.text(0.02, 0.98, stats_text,
            transform=ax.transAxes,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
            fontsize=11, fontfamily='monospace')
    
    # Add field name and source
    fig.text(0.99, 0.01, f'Field: {field} | Source: Bloomberg (Demo Data)', 
             ha='right', va='bottom', fontsize=9, style='italic', color='gray')
    
    # Add watermark
    fig.text(0.5, 0.5, 'SAMPLE DATA', 
             ha='center', va='center', fontsize=60, color='red', 
             alpha=0.1, rotation=30, transform=fig.transFigure)
    
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
        'value': f'{field} (Million JPY)'
    })
    
    # Format date as string
    export_df['Date'] = export_df['Date'].dt.strftime('%Y-%m-%d')
    
    # Calculate quarter-over-quarter growth
    export_df['QoQ Growth (%)'] = export_df[f'{field} (Million JPY)'].pct_change() * 100
    
    # Add metadata sheet
    metadata = pd.DataFrame({
        'Property': [
            'Ticker', 
            'Field', 
            'Start Date', 
            'End Date', 
            'Data Points', 
            'Frequency',
            'Latest Value',
            'Mean Value',
            '10Y Growth',
            'Retrieved',
            'Data Type'
        ],
        'Value': [
            ticker,
            field,
            df['date'].min().strftime('%Y-%m-%d'),
            df['date'].max().strftime('%Y-%m-%d'),
            len(df),
            'Quarterly',
            f"¥{df['value'].iloc[-1]:,.0f}M",
            f"¥{df['value'].mean():,.0f}M",
            f"{((df['value'].iloc[-1] - df['value'].iloc[0]) / df['value'].iloc[0] * 100):+.1f}%",
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'SAMPLE DATA (not real Bloomberg data)'
        ]
    })
    
    # Write to Excel with multiple sheets
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        export_df.to_excel(writer, sheet_name='Data', index=False)
        metadata.to_excel(writer, sheet_name='Metadata', index=False)
    
    print(f"   ✅ Data saved to: {output_file}")
    print(f"   Sheets: Data (with QoQ growth), Metadata")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""
    
    print("=" * 80)
    print("OISIX DEPRECIATION & AMORTIZATION ANALYSIS (DEMO)")
    print("=" * 80)
    print(f"\nTicker: {TICKER}")
    print(f"Field: {FIELD}")
    print(f"Output PDF: {OUTPUT_PDF}")
    print(f"Output Excel: {OUTPUT_XLSX}")
    print("\n⚠️  NOTE: This is a DEMONSTRATION using sample data")
    print("    To use real Bloomberg data:")
    print("    1. Ensure Bloomberg Terminal is running and logged in")
    print("    2. Install blpapi from Bloomberg")
    print("    3. Run plot_oisix_amortization.py instead")
    
    # Generate sample data
    print("\n" + "=" * 80)
    print("STEP 1: Generating Sample Data")
    print("=" * 80)
    
    df = generate_sample_data()
    
    # Create visualizations
    print("\n" + "=" * 80)
    print("STEP 2: Creating Visualizations")
    print("=" * 80)
    
    plot_data(df, TICKER, FIELD, OUTPUT_PDF)
    save_to_excel(df, TICKER, FIELD, OUTPUT_XLSX)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\n✅ Analysis complete!")
    print(f"\n📊 Data Summary:")
    print(f"   Ticker: {TICKER}")
    print(f"   Field: {FIELD}")
    print(f"   Data points: {len(df)} (quarterly)")
    print(f"   Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
    print(f"   Latest value: ¥{df['value'].iloc[-1]:,}M")
    print(f"   Mean value: ¥{df['value'].mean():,.0f}M")
    print(f"   10-year growth: {((df['value'].iloc[-1] - df['value'].iloc[0]) / df['value'].iloc[0] * 100):+.1f}%")
    print(f"\n📁 Output Files:")
    print(f"   Plot: {OUTPUT_PDF}")
    print(f"   Data: {OUTPUT_XLSX}")
    print("\n⚠️  REMINDER: This analysis uses SAMPLE DATA for demonstration.")
    print("=" * 80)


if __name__ == "__main__":
    main()


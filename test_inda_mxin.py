"""
=============================================================================
SCRIPT NAME: test_inda_mxin.py
=============================================================================

DESCRIPTION:
    Test script for INDA Equity and MXIN Index securities using the Bloomberg
    API via OpusBloomberg. Tests a comprehensive set of 49 fields covering
    forward consensus estimates, revision signals, dispersion, earnings
    surprise, recommendation revisions, and margin/quality metrics. Results
    are saved to a timestamped JSON file.

INPUT FILES:
    (none -- fields are defined inline from item.md instructions)

OUTPUT FILES:
    /Users/arjundivecha/Dropbox/AAA Backup/A Working/BloombergGPT/outputs/inda_mxin_test_results_<timestamp>.json
        JSON file containing all field values for each security, keyed by
        security ticker. Timestamp format is YYYYMMDD_HHMMSS.

VERSION: 1.0
LAST UPDATED: 2026-06-05
AUTHOR: Arjun Divecha

DEPENDENCIES:
    - OpusBloomberg.bbg (from /Users/arjundivecha/Dropbox/AAA Backup/A Working/OpusBloomberg)
    - pandas

USAGE:
    python test_inda_mxin.py

NOTES:
    - Bloomberg Terminal must be open and logged in.
    - Fields are queried in batches of 50 to avoid request size limits.
    - Output directory is hardcoded to /Users/arjundivecha/Dropbox/AAA Backup/A Working/BloombergGPT/outputs/.
=============================================================================
"""

import sys
sys.path.insert(0, '/Users/arjundivecha/Dropbox/AAA Backup/A Working/OpusBloomberg')

from bbg import BBG, bloomberg_setup
import pandas as pd
from datetime import datetime
import json

# Output directory
OUTPUT_DIR = '/Users/arjundivecha/Dropbox/AAA Backup/A Working/BloombergGPT/outputs'

# Securities to test
SECURITIES = ["INDA Equity", "MXIN Index"]

# Fields from item.md instructions
FIELDS = [
    # 1. Forward consensus levels
    "BEST_EPS",
    "BEST_EPS_NEXT_YR",
    "BEST_EPS_2YR",
    "BEST_EPS_3YR",
    "BEST_SALES",
    "BEST_SALES_NEXT_YR",
    "BEST_EBITDA",
    "BEST_EBIT",
    "BEST_NET_INCOME",
    "BEST_DIV_YLD",
    "BEST_DPS",
    "BEST_TARGET_PRICE",
    "BEST_LTG_EPS",
    "BEST_CAPEX",
    "BEST_BPS",
    
    # 2. Revision signals
    "EARN_REV_UP_NUM_BROKERS_1M",
    "EARN_REV_UP_NUM_BROKERS_3M",
    "EARN_REV_DN_NUM_BROKERS_1M",
    "EARN_REV_DN_NUM_BROKERS_3M",
    "EARN_REV_NUM_BROKERS_1M",
    "EARN_REV_NUM_BROKERS_3M",
    "BEST_EPS_3MO_PCT_CHG",
    "BEST_EPS_1MO_PCT_CHG",
    "BEST_SALES_3MO_PCT_CHG",
    "BEST_TARGET_PRICE_PCT_CHG_1M",
    "BEST_TARGET_PRICE_PCT_CHG_3M",
    
    # 3. Dispersion and conviction
    "BEST_EPS_STDEV",
    "BEST_EPS_HIGH",
    "BEST_EPS_LOW",
    "BEST_EPS_NUMEST",
    
    # 4. Earnings surprise / beat-miss
    "EARN_SURPRISE_PCT",
    "EARN_BEAT_RATE_LAST_4Q",
    "EPS_ESTIMATE_VS_REPORTED",
    
    # 5. Recommendation revisions
    "EQY_REC_CONS",
    "TOT_BUY_REC",
    "TOT_HOLD_REC",
    "TOT_SELL_REC",
    "BEST_ANALYST_RECS_BULLISH_PCT",
    
    # 6. Margin and quality revisions
    "BEST_OPP_MARGIN",
    "BEST_NET_MARGIN",
    "BEST_ROE",
    "BEST_ROA",
    "BEST_ROIC",
]

def load_fields():
    """Return the specific fields from item.md instructions."""
    print(f"Loaded {len(FIELDS)} fields from item.md instructions")
    return FIELDS

def test_security_fields(security, fields, batch_size=50):
    """
    Test fields for a single security in batches to avoid request size limits.
    
    Args:
        security: Bloomberg ticker
        fields: List of field mnemonics
        batch_size: Number of fields per request
    
    Returns:
        dict: Results for all fields
    """
    results = {}
    total_fields = len(fields)
    
    for i in range(0, total_fields, batch_size):
        batch = fields[i:i+batch_size]
        print(f"  Testing fields {i+1}-{min(i+batch_size, total_fields)} of {total_fields}")
        
        try:
            data = bbg.ref(security, batch)
            results.update(data)
        except Exception as e:
            print(f"  Error in batch {i//batch_size + 1}: {e}")
            for field in batch:
                results[field] = f"ERROR: {str(e)}"
    
    return results

def main():
    print("=" * 80)
    print("BLOOMBERG API TEST: INDA Equity and MXIN Index")
    print(f"Timestamp: {datetime.now()}")
    print("=" * 80)
    
    # Step 1: Setup Bloomberg connection
    print("\nStep 1: Setting up Bloomberg connection...")
    vm_ip = "10.211.55.3"  # Auto-detected from Parallels
    print(f"Using Bloomberg at {vm_ip}:8194")
    
    # Step 2: Load field catalog
    print("\nStep 2: Loading field catalog...")
    fields = load_fields()
    
    # Step 3: Test each security
    global bbg
    with BBG() as bbg:
        all_results = {}
        
        for security in SECURITIES:
            print(f"\n{'=' * 80}")
            print(f"Testing {security}")
            print(f"{'=' * 80}")
            
            results = test_security_fields(security, fields, batch_size=50)
            all_results[security] = results
            
            # Count successful vs failed fields
            successful = sum(1 for v in results.values() if v is not None and not str(v).startswith("ERROR"))
            failed = len(results) - successful
            print(f"\nResults for {security}:")
            print(f"  Successful: {successful}")
            print(f"  Failed: {failed}")
    
    # Step 4: Save results
    print("\nStep 4: Saving results...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{OUTPUT_DIR}/inda_mxin_test_results_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"Results saved to: {output_file}")
    
    # Step 5: Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for security, results in all_results.items():
        successful = sum(1 for v in results.values() if v is not None and not str(v).startswith("ERROR"))
        failed = len(results) - successful
        print(f"{security}: {successful} successful, {failed} failed")
    print("=" * 80)

if __name__ == "__main__":
    main()

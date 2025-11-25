#!/usr/bin/env python3
"""
Fix Units and Integrate into Historical Database
================================================
This script corrects the unit mismatch between extracted data and the historical database,
then integrates the new month's data.

CRITICAL: The historical database stores valueMXN in "thousands of pesos" but the
extraction outputs valueMXN in "actual pesos". This script multiplies by 1000 to fix.

Example:
- Extracted: valueMXN = 31,319,202 (31.3 million pesos)
- Historical: valueMXN = 31,319,202,025 (31.3 billion thousands = 31.3 billion pesos)
- To display in millions: divide historical by 1,000,000,000

Usage:
    python3 fix_units_and_integrate.py

Inputs:
- consar_latest_month_enriched.json: Latest month with FX/USD (in actual pesos)
- consar_siefores_with_usd.json: Historical database (in thousands of pesos)

Outputs:
- consar_siefores_with_usd.json: Updated historical database
- Backup file with timestamp
"""

import json
import shutil
from datetime import datetime
from collections import defaultdict

# === CONFIG ===
HISTORICAL_DB = "/Users/lvc/AI Scripts/2025_10 Afore JSON cleanup/consar_siefores_with_usd.json"
LATEST_MONTH = "/Users/lvc/AI Scripts/2025_10 Consar Siefore Update Agent/consar_latest_month_enriched.json"
BACKUP_DIR = "/Users/lvc/AI Scripts/2025_10 Afore JSON cleanup/backups"


def fix_units(data):
    """
    Multiply valueMXN and valueUSD by 1000 to match historical database format.

    Historical database stores:
    - valueMXN in thousands of pesos (multiply by 1000)
    - valueUSD in actual USD (multiply by 1000)

    Args:
        data: List of records with valueMXN in actual pesos and valueUSD calculated from it

    Returns:
        List of records with corrected units
    """
    print("🔧 Fixing units (multiplying valueMXN and valueUSD by 1000)...")

    for record in data:
        record['valueMXN'] = record['valueMXN'] * 1000
        record['valueUSD'] = record['valueUSD'] * 1000

    print(f"   ✓ Fixed {len(data)} records")
    return data


def integrate_into_database(historical_path, new_data, period_year, period_month):
    """
    Integrate new month data into historical database.

    Args:
        historical_path: Path to historical database
        new_data: List of new records (with fixed units)
        period_year: Year string (e.g., "2025")
        period_month: Month string (e.g., "10")
    """
    print(f"\n📚 Integrating into historical database...")

    # Load historical database
    with open(historical_path, 'r') as f:
        historical = json.load(f)

    print(f"   Loaded {len(historical)} historical records")

    # Remove any existing data for this period (in case we're re-running)
    historical_clean = [r for r in historical
                        if not (r['PeriodYear'] == period_year and r['PeriodMonth'] == period_month)]

    removed = len(historical) - len(historical_clean)
    if removed > 0:
        print(f"   ⚠️  Removed {removed} existing records for {period_month}/{period_year}")

    # Combine
    updated_db = historical_clean + new_data

    print(f"   ✓ Combined database: {len(updated_db)} records")

    # Create backup
    backup_name = f"consar_siefores_with_usd_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    backup_path = f"{BACKUP_DIR}/{backup_name}"
    shutil.copy(historical_path, backup_path)
    print(f"   ✅ Backed up to: {backup_name}")

    # Save updated database
    with open(historical_path, 'w') as f:
        json.dump(updated_db, f, indent=2, ensure_ascii=False)

    print(f"   ✅ Updated database saved")

    return updated_db


def verify_integration(database, period_year, period_month):
    """
    Verify the integration by checking AFORE totals.

    Args:
        database: Full database
        period_year: Year to verify
        period_month: Month to verify
    """
    print(f"\n✓ Verifying {period_month}/{period_year} integration...")

    # Calculate totals
    totals_mxn = defaultdict(float)
    totals_usd = defaultdict(float)
    for r in database:
        if (r['PeriodYear'] == period_year and
            r['PeriodMonth'] == period_month and
            r['Concept'] == 'Total de Activo'):
            # valueMXN is in thousands, divide by 1B to get billions
            totals_mxn[r['Afore']] += r['valueMXN'] / 1000000000
            # valueUSD is in actual USD, divide by 1M to get millions
            totals_usd[r['Afore']] += r['valueUSD'] / 1000000

    print(f"\n   AFORE Totals for {period_month}/{period_year}:")
    print("   " + "="*90)
    print(f"   {'AFORE':<20} {'MXN (billions)':>15} {'USD (millions)':>15}")
    print("   " + "-"*90)

    for afore in sorted(totals_mxn.keys()):
        print(f"   {afore:20s} {totals_mxn[afore]:15.2f} {totals_usd[afore]:15.2f}")

    print("   " + "="*90)
    print(f"   {'TOTAL':20s} {sum(totals_mxn.values()):15.2f} {sum(totals_usd.values()):15.2f}")

    return totals_mxn, totals_usd


# === MAIN EXECUTION ===
if __name__ == "__main__":
    print("="*70)
    print("Fix Units and Integrate into Historical Database")
    print("="*70)
    print()

    # Load latest month
    with open(LATEST_MONTH, 'r') as f:
        latest_data = json.load(f)

    print(f"📥 Loaded {len(latest_data)} records from latest month")

    # Get period from first record
    period_year = latest_data[0]['PeriodYear']
    period_month = latest_data[0]['PeriodMonth']
    print(f"   Period: {period_month}/{period_year}")

    # Fix units
    fixed_data = fix_units(latest_data)

    # Integrate
    updated_db = integrate_into_database(HISTORICAL_DB, fixed_data, period_year, period_month)

    # Verify
    verify_integration(updated_db, period_year, period_month)

    print()
    print("="*70)
    print("✅ Integration complete!")
    print("="*70)

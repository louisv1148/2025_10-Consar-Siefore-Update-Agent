#!/usr/bin/env python3
"""
One-time Migration: Normalize Historical Database Units
========================================================
Divides all valueMXN and valueUSD by 1,000 so the stored values
match CONSAR's native "miles de pesos" format.

Adds a "units" field ("miles_de_pesos") to every record.

This script should be run ONCE locally and is not part of the
regular pipeline.
"""

import json
import shutil
import os
from datetime import datetime

# === CONFIG ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORICAL_DB = os.path.join(SCRIPT_DIR, "../2025_10 Afore JSON cleanup/consar_siefores_with_usd.json")
BACKUP_DIR = os.path.join(SCRIPT_DIR, "backups")


def main():
    print("=" * 70)
    print("NORMALIZE HISTORICAL DATABASE UNITS")
    print("=" * 70)

    # --- Step 1: Verify DB exists ---
    if not os.path.exists(HISTORICAL_DB):
        print(f"ERROR: Historical DB not found at {HISTORICAL_DB}")
        exit(1)

    print(f"\nSource: {HISTORICAL_DB}")
    file_size = os.path.getsize(HISTORICAL_DB) / (1024 * 1024)
    print(f"File size: {file_size:.2f} MB")

    # --- Step 2: Backup ---
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"consar_siefores_BEFORE_NORMALIZATION_{timestamp}.json")
    shutil.copy2(HISTORICAL_DB, backup_path)
    print(f"Backup created: {backup_path}")

    # --- Step 3: Load ---
    print("\nLoading database...")
    with open(HISTORICAL_DB, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Total records: {len(data):,}")

    # --- Step 4: Safety check ---
    # Verify values are in the inflated range before dividing
    total_activo = [
        r for r in data
        if r.get("Concept") == "Total de Activo"
        and r.get("PeriodYear") == "2025"
        and r.get("PeriodMonth") == "11"
    ]

    if not total_activo:
        print("ERROR: Could not find Nov 2025 'Total de Activo' records for safety check")
        exit(1)

    sample_mxn = sum(r.get("valueMXN", 0) for r in total_activo)
    sample_usd = sum(r.get("valueUSD", 0) for r in total_activo)

    print(f"\n--- PRE-NORMALIZATION (Nov 2025 Total de Activo) ---")
    print(f"Sum valueMXN: {sample_mxn:,.2f}")
    print(f"Sum valueUSD: {sample_usd:,.2f}")

    # If the MXN sum is less than 1 billion, data may already be normalized
    if sample_mxn < 1_000_000_000:
        print("\nABORTING: Values appear to already be in miles de pesos range.")
        print("The database may have already been normalized.")
        exit(1)

    print(f"\nValues confirmed in inflated range (MXN sum > 1B). Proceeding.\n")

    # --- Step 5: Check for and exclude December 2025 ---
    dec_2025_count = len([
        r for r in data
        if r.get("PeriodYear") == "2025" and r.get("PeriodMonth") == "12"
    ])

    if dec_2025_count > 0:
        print(f"Found {dec_2025_count} December 2025 records — removing them.")
        data = [
            r for r in data
            if not (r.get("PeriodYear") == "2025" and r.get("PeriodMonth") == "12")
        ]
        print(f"Records after removal: {len(data):,}")

    # --- Step 6: Normalize ---
    print("Dividing valueMXN and valueUSD by 1,000...")
    for record in data:
        if isinstance(record.get("valueMXN"), (int, float)):
            record["valueMXN"] = record["valueMXN"] / 1000
        if isinstance(record.get("valueUSD"), (int, float)):
            record["valueUSD"] = record["valueUSD"] / 1000
        record["units"] = "miles_de_pesos"

    # --- Step 7: Post-normalization verification ---
    total_activo_post = [
        r for r in data
        if r.get("Concept") == "Total de Activo"
        and r.get("PeriodYear") == "2025"
        and r.get("PeriodMonth") == "11"
    ]

    post_mxn = sum(r.get("valueMXN", 0) for r in total_activo_post)
    post_usd = sum(r.get("valueUSD", 0) for r in total_activo_post)

    print(f"\n--- POST-NORMALIZATION (Nov 2025 Total de Activo) ---")
    print(f"Sum valueMXN: {post_mxn:,.2f}")
    print(f"Sum valueUSD: {post_usd:,.2f}")

    ratio = sample_mxn / post_mxn if post_mxn > 0 else 0
    print(f"Ratio (pre/post): {ratio:.1f}x")

    if abs(ratio - 1000) > 1:
        print("ERROR: Ratio is not ~1000x. Something went wrong.")
        exit(1)

    # Verify FX rates are untouched
    fx_sample = [r.get("FX_EOM", 0) for r in total_activo_post if r.get("FX_EOM", 0) > 0]
    if fx_sample:
        avg_fx = sum(fx_sample) / len(fx_sample)
        print(f"FX_EOM sample average: {avg_fx:.4f} (should be ~18-21)")
        if avg_fx < 10 or avg_fx > 30:
            print("ERROR: FX rates appear corrupted.")
            exit(1)

    # Verify units field
    units_count = sum(1 for r in data if r.get("units") == "miles_de_pesos")
    print(f"Records with 'units' field: {units_count:,} / {len(data):,}")

    # --- Step 8: Save ---
    print(f"\nSaving normalized database...")
    with open(HISTORICAL_DB, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    new_size = os.path.getsize(HISTORICAL_DB) / (1024 * 1024)
    print(f"Saved: {HISTORICAL_DB}")
    print(f"New file size: {new_size:.2f} MB")

    # --- Summary ---
    print("\n" + "=" * 70)
    print("MIGRATION COMPLETE")
    print("=" * 70)
    print(f"Records: {len(data):,}")
    print(f"Backup: {backup_path}")
    print(f"All valueMXN and valueUSD divided by 1,000")
    print(f"All records tagged with units: miles_de_pesos")
    if dec_2025_count > 0:
        print(f"Removed {dec_2025_count} December 2025 records")
    print("=" * 70)


if __name__ == "__main__":
    main()

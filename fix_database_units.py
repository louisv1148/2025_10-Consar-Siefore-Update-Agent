#!/usr/bin/env python3
"""
Fix Database Units - October & November 2025
=============================================
This script fixes the units inconsistency in the November 2025 release.

Issue: October and November 2025 data was integrated with values 1000x too small.
Fix: Multiply valueMXN and valueUSD by 1000 for all Oct & Nov 2025 records.

This will make the units consistent with the rest of the historical database.
"""

import json
import shutil
from datetime import datetime

# === CONFIG ===
INPUT_FILE = "/tmp/november_release.json"  # Downloaded from GitHub release
OUTPUT_FILE = "/Users/lvc/AI Scripts/2025_10 Afore JSON cleanup/consar_siefores_with_usd.json"
BACKUP_DIR = "/Users/lvc/AI Scripts/2025_10 Consar Siefore Update Agent/backups"


def analyze_database(data):
    """Analyze the database to confirm the issue."""
    print("\n📊 Analyzing database...")
    
    # Count records by period
    sept_2025 = [r for r in data if r.get('PeriodYear') == '2025' and r.get('PeriodMonth') == '09']
    oct_2025 = [r for r in data if r.get('PeriodYear') == '2025' and r.get('PeriodMonth') == '10']
    nov_2025 = [r for r in data if r.get('PeriodYear') == '2025' and r.get('PeriodMonth') == '11']
    
    print(f"   September 2025: {len(sept_2025)} records")
    print(f"   October 2025:   {len(oct_2025)} records")
    print(f"   November 2025:  {len(nov_2025)} records")
    
    # Check totals
    sept_total = sum(r['valueMXN'] for r in sept_2025 if r['Concept'] == 'Total de Activo')
    oct_total = sum(r['valueMXN'] for r in oct_2025 if r['Concept'] == 'Total de Activo')
    nov_total = sum(r['valueMXN'] for r in nov_2025 if r['Concept'] == 'Total de Activo')
    
    print(f"\n   Total de Activo sums:")
    print(f"   Sept: {sept_total:>20,.0f}")
    print(f"   Oct:  {oct_total:>20,.0f}  (ratio: {oct_total/sept_total:.6f}x)")
    print(f"   Nov:  {nov_total:>20,.0f}  (ratio: {nov_total/sept_total:.6f}x)")
    
    # Confirm the issue
    if oct_total / sept_total < 0.01:
        print("\n   ✅ Confirmed: Oct & Nov are ~1000x too small")
        return True
    else:
        print("\n   ⚠️  WARNING: Units appear correct already!")
        return False


def fix_units(data):
    """Fix the units for October and November 2025 records."""
    print("\n🔧 Fixing units for October & November 2025...")
    
    fixed_count = 0
    
    for record in data:
        if (record.get('PeriodYear') == '2025' and 
            record.get('PeriodMonth') in ['10', '11']):
            
            # Multiply by 1000 to match historical database format
            record['valueMXN'] = record['valueMXN'] * 1000
            record['valueUSD'] = record['valueUSD'] * 1000
            fixed_count += 1
    
    print(f"   ✅ Fixed {fixed_count} records")
    return data


def verify_fix(data):
    """Verify the fix was applied correctly."""
    print("\n✓ Verifying fix...")
    
    # Check totals again
    sept_2025 = [r for r in data if r.get('PeriodYear') == '2025' and r.get('PeriodMonth') == '09']
    oct_2025 = [r for r in data if r.get('PeriodYear') == '2025' and r.get('PeriodMonth') == '10']
    nov_2025 = [r for r in data if r.get('PeriodYear') == '2025' and r.get('PeriodMonth') == '11']
    
    sept_total = sum(r['valueMXN'] for r in sept_2025 if r['Concept'] == 'Total de Activo')
    oct_total = sum(r['valueMXN'] for r in oct_2025 if r['Concept'] == 'Total de Activo')
    nov_total = sum(r['valueMXN'] for r in nov_2025 if r['Concept'] == 'Total de Activo')
    
    print(f"\n   Total de Activo sums (after fix):")
    print(f"   Sept: {sept_total:>20,.0f}")
    print(f"   Oct:  {oct_total:>20,.0f}  (ratio: {oct_total/sept_total:.4f}x)")
    print(f"   Nov:  {nov_total:>20,.0f}  (ratio: {nov_total/sept_total:.4f}x)")
    
    # Verify ratios are reasonable (should be close to 1.0, not 0.001)
    oct_ratio = oct_total / sept_total
    nov_ratio = nov_total / sept_total
    
    if 0.8 < oct_ratio < 1.5 and 0.8 < nov_ratio < 1.5:
        print("\n   ✅ Fix verified! Ratios are now reasonable.")
        return True
    else:
        print("\n   ❌ WARNING: Ratios still look wrong!")
        return False


def create_backup(filepath):
    """Create a backup of the original file."""
    import os
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{BACKUP_DIR}/consar_siefores_BEFORE_UNITS_FIX_{timestamp}.json"
    
    shutil.copy2(filepath, backup_path)
    file_size = os.path.getsize(backup_path) / (1024 * 1024)
    
    print(f"✅ Backup created: {backup_path} ({file_size:.2f} MB)")
    return backup_path


# === MAIN EXECUTION ===
if __name__ == "__main__":
    print("=" * 70)
    print("FIX DATABASE UNITS - OCTOBER & NOVEMBER 2025")
    print("=" * 70)
    
    try:
        # Load the database
        print(f"\n📥 Loading database from: {INPUT_FILE}")
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"   Loaded {len(data):,} total records")
        
        # Analyze to confirm the issue
        needs_fix = analyze_database(data)
        
        if not needs_fix:
            print("\n⚠️  Database appears correct. Exiting without changes.")
            exit(0)
        
        # Create backup of output file if it exists
        import os
        if os.path.exists(OUTPUT_FILE):
            print(f"\n💾 Creating backup of existing file...")
            create_backup(OUTPUT_FILE)
        
        # Fix the units
        fixed_data = fix_units(data)
        
        # Verify the fix
        if not verify_fix(fixed_data):
            print("\n❌ Verification failed! Not saving changes.")
            exit(1)
        
        # Save the corrected database
        print(f"\n💾 Saving corrected database to: {OUTPUT_FILE}")
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(fixed_data, f, ensure_ascii=False, indent=2)
        
        file_size = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
        print(f"   ✅ Saved {len(fixed_data):,} records ({file_size:.2f} MB)")
        
        print("\n" + "=" * 70)
        print("✅ DATABASE UNITS FIXED SUCCESSFULLY!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Commit and push the corrected database to the history repo")
        print("2. Create a new release (v2025.11-corrected or overwrite v2025.11)")
        print("3. Update approve_and_integrate.py to apply 1000x multiplier")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise

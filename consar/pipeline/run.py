#!/usr/bin/env python3
"""
Complete CONSAR Update Pipeline
================================
Orchestrates the entire update process:
1. Check for new data and download reports
2. Extract latest month data
3. Enrich with FX and USD values
4. Verify data consistency
5. Create approval-pending file for downstream approval
"""

import json
import os
import sys
from datetime import datetime

from consar.config import PROJECT_DIR, HISTORICAL_DB, ENRICHED_JSON, APPROVAL_FILE


def run_step(step_num, total, description, func):
    """Run a pipeline step and handle errors."""
    print("\n" + "=" * 80)
    print(f"STEP {step_num}/{total}: {description}")
    print("=" * 80)

    func()

    print(f"\n✅ {description} completed successfully")


def create_approval_file():
    """Create a pending approval file from the enriched data."""
    with open(ENRICHED_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    approval_data = {
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "period_year": data[0]["PeriodYear"],
        "period_month": data[0]["PeriodMonth"],
        "total_records": len(data),
        "enriched_file": ENRICHED_JSON,
    }

    with open(APPROVAL_FILE, "w", encoding="utf-8") as f:
        json.dump(approval_data, f, indent=2)

    print(f"✅ Created approval file: {APPROVAL_FILE}")


def main():
    print("=" * 80)
    print("CONSAR SIEFORE UPDATE PIPELINE")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    if os.path.exists(HISTORICAL_DB):
        print(f"Using master DB at: {HISTORICAL_DB}")

    # Import each step (deferred to avoid loading Selenium etc. at module level)
    from consar.pipeline.download import main as download_reports
    from consar.pipeline.extract import main as extract_latest
    from consar.pipeline.enrich import main as enrich_with_fx
    from consar.pipeline.verify import main as verify_consistency

    # Step 1: Check for new data and download
    print("\n" + "=" * 80)
    print("STEP 1/4: Download Siefore reports from CONSAR")
    print("=" * 80)

    has_new_data = download_reports()

    if not has_new_data:
        print("\n" + "=" * 80)
        print("PIPELINE COMPLETE — No new data available")
        print("=" * 80)
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return

    print("\n✅ Download Siefore reports from CONSAR completed successfully")

    # Steps 2-4
    run_step(2, 4, "Extract latest month data", extract_latest)
    run_step(3, 4, "Enrich with FX and USD values", enrich_with_fx)
    run_step(4, 4, "Verify data consistency", verify_consistency)

    # Create approval file (replaces old email step)
    create_approval_file()

    # Final summary
    print("\n" + "=" * 80)
    print("PIPELINE COMPLETE")
    print("=" * 80)
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n📋 NEXT STEPS:")
    print("1. Review the pipeline summary in GitHub Actions")
    print("2. Review the enriched data file:")
    print(f"   {ENRICHED_JSON}")
    print("\n3. If approved, trigger the 'Approve Latest Data' workflow on GitHub")
    print("   Or run locally:")
    print(f"   python -m consar.approval.integrate")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()

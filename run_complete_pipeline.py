#!/usr/bin/env python3
"""
Complete CONSAR Update Pipeline
================================
Orchestrates the entire update process:
1. Check for new data and download reports
2. Extract latest month data
3. Verify data consistency
4. Enrich with FX and USD values
5. Send review email for approval

After this script completes, review the email and run:
  python3 approve_and_integrate.py
"""

import sys
import os
from datetime import datetime

from config import SCRIPT_DIR, HISTORICAL_DB, ENRICHED_JSON


def run_step(step_num, total, description, func):
    """Run a pipeline step and handle errors."""
    print("\n" + "=" * 80)
    print(f"STEP {step_num}/{total}: {description}")
    print("=" * 80)

    func()

    print(f"\n✅ {description} completed successfully")


def main():
    print("=" * 80)
    print("CONSAR SIEFORE UPDATE PIPELINE")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    if os.path.exists(HISTORICAL_DB):
        print(f"Using master DB at: {HISTORICAL_DB}")

    # Import each step (deferred to avoid loading Selenium etc. at module level)
    from consar_agent import main as download_reports
    from extract_latest_month import main as extract_latest
    from enrich_latest_month import main as enrich_with_fx
    from verify_consistency import main as verify_consistency
    from send_review_email import main as send_email

    # Steps 1-4 are required
    run_step(1, 5, "Download Siefore reports from CONSAR", download_reports)
    run_step(2, 5, "Extract latest month data", extract_latest)
    run_step(3, 5, "Enrich with FX and USD values", enrich_with_fx)
    run_step(4, 5, "Verify data consistency", verify_consistency)

    # Step 5: email is non-fatal
    try:
        run_step(5, 5, "Send review email", send_email)
    except Exception as e:
        print(f"\n⚠️  Email sending failed: {e}")
        print("    You can still review the data manually")

    # Final summary
    print("\n" + "=" * 80)
    print("PIPELINE COMPLETE")
    print("=" * 80)
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n📋 NEXT STEPS:")
    print("1. Check your email for the data review summary")
    print("2. Review the enriched data file:")
    print(f"   {ENRICHED_JSON}")
    print("\n3. If approved, run:")
    print(f"   cd \"{SCRIPT_DIR}\"")
    print(f"   python3 approve_and_integrate.py")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()

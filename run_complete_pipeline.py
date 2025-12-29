#!/usr/bin/env python3
"""
Complete CONSAR Update Pipeline
================================
Orchestrates the entire update process:
1. Check for new data and download reports
2. Extract latest month data
3. Enrich with FX and USD values
4. Send review email for approval

After this script completes, review the email and run:
  python3 approve_and_integrate.py
"""

import subprocess
import sys
import os
from datetime import datetime

# === CONFIG ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = sys.executable  # Use current python executable by default
BANXICO_TOKEN = os.getenv("BANXICO_TOKEN", "da0e20e2a0d9aaf7af1c16e60b6458a1e146f34a292889fe197274c6832fff0b")



def run_script(script_name, description, env=None):
    """Run a Python script and return success status."""
    print("\n" + "=" * 80)
    print(f"STEP: {description}")
    print("=" * 80)

    script_path = os.path.join(SCRIPT_DIR, script_name)

    # Prepare environment
    script_env = os.environ.copy()
    if env:
        script_env.update(env)

    try:
        result = subprocess.run(
            [VENV_PYTHON, script_path],
            cwd=SCRIPT_DIR,
            env=script_env,
            capture_output=False,
            text=True
        )

        if result.returncode == 0:
            print(f"\n✅ {description} completed successfully")
            return True
        else:
            print(f"\n❌ {description} failed with code {result.returncode}")
            return False

    except Exception as e:
        print(f"\n❌ Error running {script_name}: {e}")
        return False


def main():
    print("=" * 80)
    print("CONSAR SIEFORE UPDATE PIPELINE")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Step 1: Download and convert
    print("📥 STEP 1/5: Download Siefore reports from CONSAR")
    if not run_script("consar_agent.py", "Download and Convert Reports"):
        print("\n❌ Pipeline failed at Step 1")
        sys.exit(1)

    # Step 2: Extract latest month
    print("\n📊 STEP 2/5: Extract latest month data")
    if not run_script("extract_latest_month.py", "Extract Latest Month"):
        print("\n❌ Pipeline failed at Step 2")
        sys.exit(1)

    # Step 3: Enrich with FX and USD
    print("\n💱 STEP 3/5: Enrich with FX and USD values")
    env = {"BANXICO_TOKEN": BANXICO_TOKEN}
    if not run_script("enrich_latest_month.py", "Enrich with FX/USD", env=env):
        print("\n❌ Pipeline failed at Step 3")
        sys.exit(1)

    # Step 4: Verify Consistency
    print("\n✅ STEP 4/5: Verify Data Consistency")
    # Determine Master DB path: check env var, then assume sibling directory structure if running locally
    master_db_env = {}
    
    # If we are running in CI/CD, we might pass MASTER_DB_PATH
    # If running locally, we might default to the "Afore JSON cleanup" folder if it exists
    local_master_db = os.path.join(os.path.dirname(SCRIPT_DIR), "2025_10 Afore JSON cleanup", "consar_siefores_with_usd.json")
    if os.path.exists(local_master_db):
        master_db_env["MASTER_DB_PATH"] = local_master_db
        print(f"   Using local master DB at: {local_master_db}")
    
    if not run_script("verify_consistency.py", "Verify Data Consistency", env=master_db_env):
        print("\n❌ Pipeline failed consistency check (Step 4)")
        sys.exit(1)

    # Step 5: Send review email
    print("\n📧 STEP 5/5: Send review email")
    if not run_script("send_review_email.py", "Send Review Email"):
        print("\n⚠️  Email sending failed (may not be configured)")
        print("    You can still review the data manually")

    # Final summary
    print("\n" + "=" * 80)
    print("PIPELINE COMPLETE")
    print("=" * 80)
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n📋 NEXT STEPS:")
    print("1. Check your email for the data review summary")
    print("2. Review the enriched data file:")
    print(f"   {os.path.join(SCRIPT_DIR, 'consar_latest_month_enriched.json')}")
    print("\n3. If approved, run:")
    print(f"   cd \"{SCRIPT_DIR}\"")
    print(f"   python3 approve_and_integrate.py")
    print("\nNote: Integration script will ask for master database location if not found.")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()

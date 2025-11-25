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
SCRIPT_DIR = "/Users/lvc/AI Scripts/2025_10 Consar Siefore Update Agent"
VENV_PYTHON = os.path.join(SCRIPT_DIR, "venv/bin/python3")
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
    print("📥 STEP 1/4: Download Siefore reports from CONSAR")
    if not run_script("consar_agent.py", "Download and Convert Reports"):
        print("\n❌ Pipeline failed at Step 1")
        sys.exit(1)

    # Step 2: Extract latest month
    print("\n📊 STEP 2/4: Extract latest month data")
    if not run_script("extract_latest_month.py", "Extract Latest Month"):
        print("\n❌ Pipeline failed at Step 2")
        sys.exit(1)

    # Step 3: Enrich with FX and USD
    print("\n💱 STEP 3/4: Enrich with FX and USD values")
    env = {"BANXICO_TOKEN": BANXICO_TOKEN}
    if not run_script("enrich_latest_month.py", "Enrich with FX/USD", env=env):
        print("\n❌ Pipeline failed at Step 3")
        sys.exit(1)

    # Step 4: Send review email
    print("\n📧 STEP 4/4: Send review email")
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
    print(f"   {SCRIPT_DIR}/consar_latest_month_enriched.json")
    print("\n3. If approved, run:")
    print(f"   cd \"{SCRIPT_DIR}\"")
    print(f"   python3 approve_and_integrate.py")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()

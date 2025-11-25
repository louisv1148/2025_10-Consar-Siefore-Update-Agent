#!/usr/bin/env python3
"""
Approve and Integrate Data
===========================
After reviewing the emailed summary, run this script to:
1. Mark the data as approved
2. Integrate into historical database
3. Create a new GitHub release with the updated data

This script should be run AFTER reviewing the email summary.
"""

import json
import os
import shutil
from datetime import datetime
from dotenv import load_dotenv

# === CONFIG ===
APPROVAL_FILE = "/Users/lvc/AI Scripts/2025_10 Consar Siefore Update Agent/approval_pending.json"
ENRICHED_JSON = "/Users/lvc/AI Scripts/2025_10 Consar Siefore Update Agent/consar_latest_month_enriched.json"
HISTORICAL_DB = "/Users/lvc/AI Scripts/2025_10 Afore JSON cleanup/consar_siefores_with_usd.json"
BACKUP_DIR = "/Users/lvc/AI Scripts/2025_10 Consar Siefore Update Agent/backups"

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def check_approval_pending():
    """Check if there's a pending approval."""
    if not os.path.exists(APPROVAL_FILE):
        print("❌ No pending approval found")
        print("   Run send_review_email.py first")
        return None

    with open(APPROVAL_FILE, "r") as f:
        approval = json.load(f)

    if approval.get("status") != "pending":
        print(f"❌ Approval status is '{approval.get('status')}', not 'pending'")
        return None

    return approval


def display_summary(approval):
    """Display summary for final confirmation."""
    print("\n" + "=" * 70)
    print("DATA READY FOR INTEGRATION")
    print("=" * 70)
    print(f"\nPeriod: {approval['period_month']}/{approval['period_year']}")
    print(f"Records: {approval['total_records']:,}")
    print(f"Created: {approval['created_at']}")
    print(f"\nSource: {approval['enriched_file']}")
    print(f"Target: {HISTORICAL_DB}")
    print("=" * 70)


def backup_historical_db():
    """Create backup of historical database."""
    if not os.path.exists(HISTORICAL_DB):
        print("⚠️  No historical database found - will create new one")
        return None

    os.makedirs(BACKUP_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"consar_siefores_backup_{timestamp}.json")

    shutil.copy2(HISTORICAL_DB, backup_path)
    file_size = os.path.getsize(backup_path) / (1024 * 1024)

    print(f"✅ Backup created: {backup_path} ({file_size:.2f} MB)")
    return backup_path


def integrate_data():
    """Integrate new data into historical database."""
    print("\n📊 Integrating data...")

    # Load new data
    with open(ENRICHED_JSON, "r", encoding="utf-8") as f:
        new_data = json.load(f)

    print(f"   Loaded {len(new_data):,} new records")

    # Load historical data or create empty list
    if os.path.exists(HISTORICAL_DB):
        with open(HISTORICAL_DB, "r", encoding="utf-8") as f:
            historical_data = json.load(f)
        print(f"   Loaded {len(historical_data):,} historical records")
    else:
        historical_data = []
        print(f"   No historical data found - creating new database")

    # Get the new period
    new_period = (new_data[0]["PeriodYear"], new_data[0]["PeriodMonth"])

    # Remove any existing records for this period (in case of re-run)
    historical_data = [
        r for r in historical_data
        if (r.get("PeriodYear"), r.get("PeriodMonth")) != new_period
    ]

    initial_count = len(historical_data)

    # Add new data
    historical_data.extend(new_data)

    print(f"   Removed existing records for {new_period[1]}/{new_period[0]}: {initial_count - (len(historical_data) - len(new_data))}")
    print(f"   Added {len(new_data):,} new records")
    print(f"   Total records: {len(historical_data):,}")

    # Save updated database
    with open(HISTORICAL_DB, "w", encoding="utf-8") as f:
        json.dump(historical_data, f, ensure_ascii=False, indent=2)

    file_size = os.path.getsize(HISTORICAL_DB) / (1024 * 1024)
    print(f"✅ Historical database updated ({file_size:.2f} MB)")

    return len(new_data), len(historical_data)


def update_approval_status(backup_path, new_count, total_count):
    """Mark approval as completed."""
    with open(APPROVAL_FILE, "r") as f:
        approval = json.load(f)

    approval["status"] = "approved"
    approval["approved_at"] = datetime.now().isoformat()
    approval["backup_file"] = backup_path
    approval["new_records_added"] = new_count
    approval["total_records_in_db"] = total_count

    with open(APPROVAL_FILE, "w") as f:
        json.dump(approval, f, indent=2)

    print(f"✅ Approval status updated")


def prompt_github_release(approval):
    """Prompt user to create GitHub release."""
    print("\n" + "=" * 70)
    print("NEXT STEP: CREATE GITHUB RELEASE")
    print("=" * 70)

    month_names = {
        "01": "January", "02": "February", "03": "March", "04": "April",
        "05": "May", "06": "June", "07": "July", "08": "August",
        "09": "September", "10": "October", "11": "November", "12": "December"
    }
    month_name = month_names.get(approval["period_month"], approval["period_month"])

    tag = f"v{approval['period_year']}.{approval['period_month']}"

    print(f"\nTo create a GitHub release for this data:")
    print(f"\n1. Tag: {tag}")
    print(f"2. Title: {month_name} {approval['period_year']} - Siefore Data Update")
    print(f"3. Description:")
    print(f"   Updated CONSAR Siefore data for {month_name} {approval['period_year']}")
    print(f"   - {approval['total_records']:,} new records")
    print(f"   - FX enriched and USD values calculated")
    print(f"\n4. Run the GitHub release script:")
    print(f"   python3 create_github_release.py")
    print("\n" + "=" * 70)


# === MAIN EXECUTION ===
if __name__ == "__main__":
    print("=" * 70)
    print("APPROVE AND INTEGRATE DATA")
    print("=" * 70)

    try:
        # Check for pending approval
        approval = check_approval_pending()
        if not approval:
            exit(1)

        # Display summary
        display_summary(approval)

        # Running this script signals approval
        print("\n✅ Proceeding with integration...")
        print("   (Running this script signals approval)")
        print("   (Press Ctrl+C within 3 seconds to cancel)")

        import time
        try:
            time.sleep(3)
        except KeyboardInterrupt:
            print("\n\n❌ Integration cancelled by user")
            exit(0)

        # Backup historical database
        backup_path = backup_historical_db()

        # Integrate data
        new_count, total_count = integrate_data()

        # Update approval status
        update_approval_status(backup_path, new_count, total_count)

        print("\n✅ INTEGRATION COMPLETE!")

        # Prompt for GitHub release
        prompt_github_release(approval)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise

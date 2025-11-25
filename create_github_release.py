#!/usr/bin/env python3
"""
Create GitHub Release
=====================
Automatically creates a GitHub release for the newly integrated data.

This script:
1. Reads the approval file to get period information
2. Creates a git tag (v2025.09 format)
3. Creates GitHub release with proper title and description
4. Optionally uploads the database file as a release asset

Requires:
- GitHub CLI (gh) installed and authenticated
- Or GITHUB_TOKEN environment variable set
"""

import json
import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# === CONFIG ===
APPROVAL_FILE = "/Users/lvc/AI Scripts/2025_10 Consar Siefore Update Agent/approval_pending.json"
DATABASE_FILE = "/Users/lvc/AI Scripts/2025_10 Afore JSON cleanup/consar_siefores_with_usd.json"
REPO_OWNER = "louisv1148"
REPO_NAME = "2025_10-Afore-JSON-cleanup"

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def load_approval_data():
    """Load approval data to get release information."""
    if not os.path.exists(APPROVAL_FILE):
        raise FileNotFoundError("No approval file found. Run approve_and_integrate.py first.")

    with open(APPROVAL_FILE, "r") as f:
        approval = json.load(f)

    if approval.get("status") != "approved":
        raise ValueError(f"Data not approved. Status: {approval.get('status')}")

    return approval


def check_gh_cli():
    """Check if GitHub CLI is installed and authenticated."""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def create_release_with_gh_cli(tag, title, body):
    """Create release using GitHub CLI."""
    print("📦 Creating release with GitHub CLI...")

    cmd = [
        "gh", "release", "create", tag,
        "--title", title,
        "--notes", body,
        "--repo", f"{REPO_OWNER}/{REPO_NAME}"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print(f"✅ Release created successfully!")
            print(f"   URL: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Error creating release: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Release creation timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def create_release_with_api(tag, title, body):
    """Create release using GitHub API."""
    import requests

    print("📦 Creating release with GitHub API...")

    if not GITHUB_TOKEN:
        raise ValueError(
            "GITHUB_TOKEN not found. Either:\n"
            "1. Install and authenticate GitHub CLI (gh)\n"
            "2. Set GITHUB_TOKEN environment variable"
        )

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    data = {
        "tag_name": tag,
        "name": title,
        "body": body,
        "draft": False,
        "prerelease": False
    }

    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        response.raise_for_status()

        release_url = response.json().get("html_url")
        print(f"✅ Release created successfully!")
        print(f"   URL: {release_url}")
        return True

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"   Response: {response.text}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def generate_release_notes(approval):
    """Generate release notes body."""

    month_names = {
        "01": "January", "02": "February", "03": "March", "04": "April",
        "05": "May", "06": "June", "07": "July", "08": "August",
        "09": "September", "10": "October", "11": "November", "12": "December"
    }

    month_name = month_names.get(approval["period_month"], approval["period_month"])

    # Get file size
    file_size_mb = os.path.getsize(DATABASE_FILE) / (1024 * 1024)

    # Load enriched data for statistics
    with open(approval["enriched_file"], "r") as f:
        enriched_data = json.load(f)

    total_mxn = sum(r.get("valueMXN", 0) for r in enriched_data)
    total_usd = sum(r.get("valueUSD", 0) for r in enriched_data)
    fx_rate = enriched_data[0].get("FX_EOM", 0)

    afores = sorted(set(r["Afore"] for r in enriched_data))
    siefores = sorted(set(r["Siefore"] for r in enriched_data))

    body = f"""# {month_name} {approval['period_year']} - CONSAR Siefore Data Update

Updated pension fund (AFORE) holdings data from CONSAR with FX enrichment.

## 📊 Data Summary

- **Period:** {month_name} {approval['period_year']}
- **Records Added:** {approval['new_records_added']:,}
- **Total Database Records:** {approval['total_records_in_db']:,}
- **Database Size:** {file_size_mb:.2f} MB

## 💰 Financial Summary

- **Total Assets (MXN):** ${total_mxn:,.0f}
- **Total Assets (USD):** ${total_usd:,.0f}
- **FX Rate (EOM):** {fx_rate:.4f} MXN/USD

## 🏢 Coverage

- **AFOREs ({len(afores)}):** {', '.join(afores)}
- **SIEFOREs ({len(siefores)}):** {', '.join(siefores)}

## 📈 Concepts Tracked

- Total de Activo
- Inversiones Tercerizadas
- Inversión en títulos Fiduciarios
- Inversión en Fondos Mutuos

## 🔧 Data Processing

1. ✅ Downloaded from CONSAR SISNET
2. ✅ Extracted and validated
3. ✅ Enriched with Banxico FX rates
4. ✅ USD values calculated
5. ✅ Integrated into historical database

## 📁 Files

The complete database is available in this repository:
- `consar_siefores_with_usd.json` - Full historical database with USD values

---

🤖 Generated by [CONSAR Siefore Update Agent](https://github.com/{REPO_OWNER}/2025_10-Consar-Siefore-Update-Agent)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

    return body


# === MAIN EXECUTION ===
if __name__ == "__main__":
    print("=" * 70)
    print("CREATE GITHUB RELEASE")
    print("=" * 70)

    try:
        # Load approval data
        print("\n📋 Loading approval data...")
        approval = load_approval_data()

        period_month = approval["period_month"]
        period_year = approval["period_year"]

        month_names = {
            "01": "January", "02": "February", "03": "March", "04": "April",
            "05": "May", "06": "June", "07": "July", "08": "August",
            "09": "September", "10": "October", "11": "November", "12": "December"
        }
        month_name = month_names.get(period_month, period_month)

        # Generate release information
        tag = f"v{period_year}.{period_month}"
        title = f"{month_name} {period_year} - Siefore Data Update"
        body = generate_release_notes(approval)

        print(f"   Period: {month_name} {period_year}")
        print(f"   Tag: {tag}")
        print(f"   Records: {approval['new_records_added']:,}")

        # Check for GitHub CLI
        has_gh_cli = check_gh_cli()

        if has_gh_cli:
            print("\n✅ GitHub CLI detected and authenticated")
            success = create_release_with_gh_cli(tag, title, body)
        else:
            print("\n⚠️  GitHub CLI not available, using API")
            success = create_release_with_api(tag, title, body)

        if success:
            print("\n" + "=" * 70)
            print("RELEASE CREATED SUCCESSFULLY")
            print("=" * 70)
            print(f"\n✅ Tag: {tag}")
            print(f"✅ Title: {title}")
            print(f"✅ Records: {approval['new_records_added']:,} added")
            print(f"\n🔗 View release at:")
            print(f"   https://github.com/{REPO_OWNER}/{REPO_NAME}/releases/tag/{tag}")
            print("\n" + "=" * 70)
        else:
            print("\n❌ Failed to create release")
            exit(1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise

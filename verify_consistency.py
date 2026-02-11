
import json
import pandas as pd
import sys
import os

from config import ENRICHED_JSON, HISTORICAL_DB, CONSISTENCY_REPORT

# Paths
LATEST_FILE = ENRICHED_JSON
MASTER_FILE = HISTORICAL_DB

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_latest_period(data):
    """Find the most recent (year, month) period in the dataset."""
    periods = set()
    for r in data:
        y = r.get("PeriodYear", "")
        m = r.get("PeriodMonth", "")
        if y and m:
            periods.add((y, m))
    if not periods:
        return None, None
    latest = max(periods, key=lambda p: (p[0], p[1]))
    return latest

def check_set_diff(name, set_latest, set_prior):
    missing = set_prior - set_latest
    new = set_latest - set_prior
    status = "pass"
    msg = f"{name} match perfectly"

    if missing or new:
        status = "warn"
        msg = f"Missing: {len(missing)}, New: {len(new)}"
        if missing: print(f"⚠️  Missing {name} in latest: {missing}")
        if new: print(f"ℹ️  New {name} in latest: {new}")
    else:
        print(f"✅ {name} match perfectly.")

    return {"name": f"{name} Integrity", "status": status, "message": msg}


def main():
    print("Loading data...")
    latest_data = load_json(LATEST_FILE)
    master_data = load_json(MASTER_FILE)

    # Determine periods dynamically
    latest_year = latest_data[0].get("PeriodYear", "unknown")
    latest_month = latest_data[0].get("PeriodMonth", "unknown")

    prior_year, prior_month = find_latest_period(master_data)
    if not prior_year:
        raise ValueError("No periods found in master database.")

    prior_data = [
        r for r in master_data
        if r.get("PeriodYear") == prior_year and r.get("PeriodMonth") == prior_month
    ]

    print(f"Latest Records ({latest_month}/{latest_year}): {len(latest_data)}")
    print(f"Prior Records ({prior_month}/{prior_year}): {len(prior_data)}")

    if not prior_data:
        raise ValueError(f"No {prior_month}/{prior_year} data found in master file.")

    # Convert to DataFrame for easier analysis
    df_latest = pd.DataFrame(latest_data)
    df_prior = pd.DataFrame(prior_data)

    # Report Data
    report = {
        "status": "pass",
        "checks": []
    }

    # --- Check 1: Record Counts ---
    print("\n--- 1. Record Count Consistency ---")
    count_check = {
        "name": "Record Count",
        "latest": len(latest_data),
        "prior": len(prior_data),
        "status": "pass" if len(latest_data) == len(prior_data) else "fail"
    }
    if len(latest_data) == len(prior_data):
        print(f"✅ Record counts match: {len(latest_data)}")
    else:
        print(f"⚠️  Mismatch: Latest={len(latest_data)} vs Prior={len(prior_data)}")
    report["checks"].append(count_check)

    # --- Check 2: Entity Completeness ---
    print("\n--- 2. Entity Completeness ---")
    report["checks"].append(check_set_diff("Afores", set(df_latest["Afore"]), set(df_prior["Afore"])))
    report["checks"].append(check_set_diff("Siefores", set(df_latest["Siefore"]), set(df_prior["Siefore"])))
    report["checks"].append(check_set_diff("Concepts", set(df_latest["Concept"]), set(df_prior["Concept"])))

    # --- Check 3: Order of Magnitude (Total Assets) ---
    print("\n--- 3. Total Assets Comparison (USD) ---")
    total_concept = "Total de Activo"
    latest_assets = df_latest[df_latest["Concept"] == total_concept]["valueUSD"].sum()
    prior_assets = df_prior[df_prior["Concept"] == total_concept]["valueUSD"].sum()

    diff = latest_assets - prior_assets
    pct_change = (diff / prior_assets) * 100 if prior_assets else 0

    print(f"Prior ({prior_month}/{prior_year}): ${prior_assets:,.2f}")
    print(f"Latest ({latest_month}/{latest_year}): ${latest_assets:,.2f}")
    print(f"Change: ${diff:,.2f} ({pct_change:+.2f}%)")

    asset_status = "pass"
    if abs(pct_change) > 10:
        print("⚠️  Warning: Large variance (>10%) in Total Assets.")
        asset_status = "warn"
    else:
        print("✅ Order of magnitude is consistent (variance < 10%).")

    report["checks"].append({
        "name": "Total Assets (USD)",
        "prior": prior_assets,
        "latest": latest_assets,
        "change_pct": pct_change,
        "status": asset_status
    })

    # Save Report
    with open(CONSISTENCY_REPORT, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n📝 Report saved to {CONSISTENCY_REPORT}")

    # --- Check 4: Detailed Breakdown by Afore ---
    print(f"\n--- 4. Afore Asset Breakdown (USD Millions) ---")
    print(f"{'Afore':<15} {'Prior':>12} {'Latest':>12} {'Change':>10}")
    print("-" * 55)

    afores = sorted(list(set(df_latest["Afore"]) | set(df_prior["Afore"])))
    for afore in afores:
        v_latest = df_latest[(df_latest["Afore"] == afore) & (df_latest["Concept"] == total_concept)]["valueUSD"].sum() / 1e6
        v_prior = df_prior[(df_prior["Afore"] == afore) & (df_prior["Concept"] == total_concept)]["valueUSD"].sum() / 1e6

        change = v_latest - v_prior
        pct = (change / v_prior * 100) if v_prior > 0 else 0

        print(f"{afore:<15} {v_prior:>12,.1f} {v_latest:>12,.1f} {pct:>9.1f}%")

    print("-" * 55)


if __name__ == "__main__":
    main()

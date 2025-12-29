
import json
import pandas as pd
import sys
import os

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LATEST_FILE = os.path.join(SCRIPT_DIR, "consar_latest_month_enriched.json")
# Default to master file in the same directory, or override via env var
MASTER_FILE = os.environ.get("MASTER_DB_PATH", os.path.join(SCRIPT_DIR, "consar_siefores_with_usd_updated.json"))

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

print("Loading data...")
latest_data = load_json(LATEST_FILE)
master_data = load_json(MASTER_FILE)

# Filter Master for Oct 2025 (Prior Month)
prior_data = [
    r for r in master_data 
    if r.get("PeriodYear") == "2025" and r.get("PeriodMonth") == "10"
]

print(f"Latest Records (Nov 2025): {len(latest_data)}")
print(f"Prior Records (Oct 2025): {len(prior_data)}")

if not prior_data:
    print("❌ Critical: No October 2025 data found in master file.")
    sys.exit(1)

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
    print(f"⚠️  Mismatch: Nov={len(latest_data)} vs Oct={len(prior_data)}")
report["checks"].append(count_check)

# --- Check 2: Entity Completeness ---
print("\n--- 2. Entity Completeness ---")
def check_set_diff(name, set_latest, set_prior):
    missing = set_prior - set_latest
    new = set_latest - set_prior
    status = "pass"
    msg = f"{name} match perfectly"
    
    if missing or new:
        status = "warn"
        msg = f"Missing: {len(missing)}, New: {len(new)}"
        if missing: print(f"⚠️  Missing {name} in Nov: {missing}")
        if new: print(f"ℹ️  New {name} in Nov: {new}")
    else:
        print(f"✅ {name} match perfectly.")
        
    return {"name": f"{name} Integrity", "status": status, "message": msg}

report["checks"].append(check_set_diff("Afores", set(df_latest["Afore"]), set(df_prior["Afore"])))
report["checks"].append(check_set_diff("Siefores", set(df_latest["Siefore"]), set(df_prior["Siefore"])))
report["checks"].append(check_set_diff("Concepts", set(df_latest["Concept"]), set(df_prior["Concept"])))

# --- Check 3: Order of Magnitude (Total Assets) ---
print("\n--- 3. Total Assets Comparison (USD) ---")
# Filter for "Total de Activo" only to avoid double counting
total_concept = "Total de Activo"
latest_assets = df_latest[df_latest["Concept"] == total_concept]["valueUSD"].sum()
prior_assets = df_prior[df_prior["Concept"] == total_concept]["valueUSD"].sum()

diff = latest_assets - prior_assets
pct_change = (diff / prior_assets) * 100 if prior_assets else 0

print(f"Oct (Prior): ${prior_assets:,.2f}")
print(f"Nov (Latest): ${latest_assets:,.2f}")
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
report_path = os.path.join(SCRIPT_DIR, "consistency_report.json")
with open(report_path, "w") as f:
    json.dump(report, f, indent=2)
print(f"\n📝 Report saved to {report_path}")

# --- Check 4: Detailed Breakdown by Afore ---
print("\n--- 4. Afore Asset Breakdown (USD Millions) ---")
print(f"{'Afore':<15} {'Oct 2025':>12} {'Nov 2025':>12} {'Change':>10}")
print("-" * 55)

afores = sorted(list(set(df_latest["Afore"]) | set(df_prior["Afore"])))
for afore in afores:
    v_latest = df_latest[(df_latest["Afore"] == afore) & (df_latest["Concept"] == total_concept)]["valueUSD"].sum() / 1e6
    v_prior = df_prior[(df_prior["Afore"] == afore) & (df_prior["Concept"] == total_concept)]["valueUSD"].sum() / 1e6
    
    change = v_latest - v_prior
    pct = (change / v_prior * 100) if v_prior > 0 else 0
    
    print(f"{afore:<15} {v_latest:>12,.1f} {v_prior:>12,.1f} {pct:>9.1f}%")

print("-" * 55)

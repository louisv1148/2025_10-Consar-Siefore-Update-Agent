
import json
import pandas as pd
import sys

# Paths
LATEST_FILE = "/Users/lvc/AI Scripts/2025_10 Consar Siefore Update Agent/consar_latest_month_enriched.json"
MASTER_FILE = "/Users/lvc/AI Scripts/2025_10 Consar Siefore Update Agent/consar_siefores_with_usd_updated.json"

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

# --- Check 1: Record Counts ---
print("\n--- 1. Record Count Consistency ---")
if len(latest_data) == len(prior_data):
    print(f"✅ Record counts match: {len(latest_data)}")
else:
    print(f"⚠️  Mismatch: Nov={len(latest_data)} vs Oct={len(prior_data)}")

# --- Check 2: Afore/Siefore Completeness ---
print("\n--- 2. Entity Completeness ---")
def check_set_diff(name, set_latest, set_prior):
    missing = set_prior - set_latest
    new = set_latest - set_prior
    if not missing and not new:
        print(f"✅ {name} match perfectly.")
    else:
        if missing: print(f"⚠️  Missing {name} in Nov: {missing}")
        if new: print(f"ℹ️  New {name} in Nov: {new}")

check_set_diff("Afores", set(df_latest["Afore"]), set(df_prior["Afore"]))
check_set_diff("Siefores", set(df_latest["Siefore"]), set(df_prior["Siefore"]))
check_set_diff("Concepts", set(df_latest["Concept"]), set(df_prior["Concept"]))

# --- Check 3: Order of Magnitude (Total Assets) ---
print("\n--- 3. Total Assets Comparison (USD) ---")
# Filter for "Total de Activo" only to avoid double counting
total_concept = "Total de Activo"
latest_assets = df_latest[df_latest["Concept"] == total_concept]["valueUSD"].sum()
prior_assets = df_prior[df_prior["Concept"] == total_concept]["valueUSD"].sum()

print(f"Oct 2025 (Prior): ${prior_assets:,.2f}")
print(f"Nov 2025 (Latest): ${latest_assets:,.2f}")

diff = latest_assets - prior_assets
pct_change = (diff / prior_assets) * 100 if prior_assets else 0

print(f"Change: ${diff:,.2f} ({pct_change:+.2f}%)")

if abs(pct_change) > 10:
    print("⚠️  Warning: Large variance (>10%) in Total Assets.")
else:
    print("✅ Order of magnitude is consistent (variance < 10%).")

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

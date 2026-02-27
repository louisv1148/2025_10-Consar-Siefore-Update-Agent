#!/usr/bin/env python3
"""
Generate a markdown summary for GitHub Actions step summary.
Reads pipeline output files and prints markdown to stdout.
"""

import json
import os
from consar.config import (
    APPROVAL_FILE, ENRICHED_JSON, CONSISTENCY_REPORT,
    METADATA_FILE, MONTHS_EN
)


def main():
    # Check if pipeline produced data
    if not os.path.exists(APPROVAL_FILE):
        print("## Pipeline Result")
        print("No new data available from CONSAR.")
        return

    with open(APPROVAL_FILE) as f:
        approval = json.load(f)

    period_year = approval.get("period_year", "?")
    period_month = approval.get("period_month", "?")
    month_name = MONTHS_EN.get(period_month, period_month)

    # Header
    print(f"## CONSAR Data Review: {month_name} {period_year}")
    print()

    # Overview
    print("### Overview")
    print(f"- **Period:** {month_name} {period_year}")
    print(f"- **Total Records:** {approval.get('total_records', '?'):,}")
    print(f"- **Status:** `{approval.get('status', '?')}`")
    print()

    # Enriched data summary (Total de Activo only)
    if os.path.exists(ENRICHED_JSON):
        with open(ENRICHED_JSON) as f:
            enriched = json.load(f)

        total_activo = [r for r in enriched if r.get("Concept") == "Total de Activo"]
        total_mxn = sum(r.get("valueMXN", 0) for r in total_activo)
        total_usd = sum(r.get("valueUSD", 0) for r in total_activo)
        fx_rate = enriched[0].get("FX_EOM", 0) if enriched else 0

        print("### Financial Summary")
        print(f"- **Total Assets (MXN):** ${total_mxn:,.0f} miles de pesos")
        print(f"- **Total Assets (USD):** ${total_usd:,.0f} miles de USD")
        print(f"- **FX Rate (EOM):** {fx_rate:.4f} MXN/USD")
        print()

        # Per-Afore breakdown
        print("### AUM by Afore (Total de Activo, USD millions)")
        print()
        print("| Afore | USD (M) |")
        print("|-------|--------:|")
        afore_totals = {}
        for r in total_activo:
            afore = r.get("Afore", "?")
            afore_totals[afore] = afore_totals.get(afore, 0) + r.get("valueUSD", 0)
        for afore in sorted(afore_totals):
            val = afore_totals[afore] / 1000  # miles -> millions
            print(f"| {afore} | ${val:,.0f}M |")
        market_total = sum(afore_totals.values()) / 1000
        print(f"| **TOTAL** | **${market_total:,.0f}M** |")
        print()

    # Consistency checks
    if os.path.exists(CONSISTENCY_REPORT):
        with open(CONSISTENCY_REPORT) as f:
            report = json.load(f)

        print("### Consistency Checks")
        print()
        print("| Check | Status | Details |")
        print("|-------|--------|---------|")
        for check in report.get("checks", []):
            icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}.get(check["status"], "?")
            name = check["name"]

            if "change_pct" in check:
                details = f"{check['change_pct']:+.2f}% (Prior: ${check['prior']:,.0f})"
            elif "latest" in check and "prior" in check:
                details = f"{check['latest']} vs {check['prior']}"
            elif "message" in check:
                details = check["message"]
            else:
                details = ""

            print(f"| {name} | {icon} | {details} |")
        print()

    # Action required
    print("### Next Step")
    print("If the data looks correct, go to **Actions > Approve Latest Data > Run workflow** to integrate and generate reports.")


if __name__ == "__main__":
    main()

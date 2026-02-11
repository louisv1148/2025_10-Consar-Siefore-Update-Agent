#!/usr/bin/env python3
"""
Generate YTD comparison tables for Afore assets
Compares December 2024 vs October 2025
"""

import json
from collections import defaultdict

DB_PATH = "/Users/lvc/AI Scripts/2025_10 Afore JSON cleanup/consar_siefores_with_usd.json"

def load_data():
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def aggregate_by_afore(data, year, month, concept):
    """Aggregate values by Afore for a specific period and concept

    Note: Handles both accented and non-accented versions of concepts
    due to data inconsistencies between periods
    """
    result = defaultdict(lambda: {'MXN': 0, 'USD': 0, 'FX': 0})

    # Normalize concept for matching (handle accent variations)
    concepts_to_match = [concept]
    if concept == "Inversion en Fondos Mutuos":
        concepts_to_match.append("Inversión en Fondos Mutuos")
    elif concept == "Inversión en Fondos Mutuos":
        concepts_to_match.append("Inversion en Fondos Mutuos")

    for record in data:
        if (record['PeriodYear'] == year and
            record['PeriodMonth'] == month and
            record['Concept'] in concepts_to_match):
            afore = record['Afore']
            result[afore]['MXN'] += record['valueMXN']
            result[afore]['USD'] += record['valueUSD']
            result[afore]['FX'] = record['FX_EOM']

    return dict(result)

def format_number(num, decimals=0):
    """Format number with commas"""
    if decimals == 0:
        return f"{int(num):,}"
    return f"{num:,.{decimals}f}"

def print_comparison_table(title, dec_data, oct_data):
    """Print comparison table for a specific category"""
    print(f"\n## {title}")
    print("| Afore | Dec 2024 MXN (M) | Oct 2025 MXN (M) | Growth MXN (M) | Growth % | Dec 2024 USD (M) | Oct 2025 USD (M) | Growth USD (M) | Growth % |")
    print("|-------|----------------:|----------------:|--------------:|---------:|----------------:|----------------:|--------------:|---------:|")

    # Get all Afores
    all_afores = sorted(set(list(dec_data.keys()) + list(oct_data.keys())))

    total_dec_mxn = 0
    total_oct_mxn = 0
    total_dec_usd = 0
    total_oct_usd = 0

    for afore in all_afores:
        dec_mxn = dec_data.get(afore, {}).get('MXN', 0) / 1000  # Convert to millions
        oct_mxn = oct_data.get(afore, {}).get('MXN', 0) / 1000
        dec_usd = dec_data.get(afore, {}).get('USD', 0) / 1_000_000  # Convert to millions
        oct_usd = oct_data.get(afore, {}).get('USD', 0) / 1_000_000

        growth_mxn = oct_mxn - dec_mxn
        growth_usd = oct_usd - dec_usd

        pct_mxn = (growth_mxn / dec_mxn * 100) if dec_mxn > 0 else 0
        pct_usd = (growth_usd / dec_usd * 100) if dec_usd > 0 else 0

        total_dec_mxn += dec_mxn
        total_oct_mxn += oct_mxn
        total_dec_usd += dec_usd
        total_oct_usd += oct_usd

        print(f"| {afore} | {format_number(dec_mxn)} | {format_number(oct_mxn)} | "
              f"{format_number(growth_mxn)} | {pct_mxn:.1f}% | "
              f"${format_number(dec_usd, 2)} | ${format_number(oct_usd, 2)} | "
              f"${format_number(growth_usd, 2)} | {pct_usd:.1f}% |")

    # Print totals
    total_growth_mxn = total_oct_mxn - total_dec_mxn
    total_growth_usd = total_oct_usd - total_dec_usd
    total_pct_mxn = (total_growth_mxn / total_dec_mxn * 100) if total_dec_mxn > 0 else 0
    total_pct_usd = (total_growth_usd / total_dec_usd * 100) if total_dec_usd > 0 else 0

    print("|-------|----------------:|----------------:|--------------:|---------:|----------------:|----------------:|--------------:|---------:|")
    print(f"| **TOTAL** | **{format_number(total_dec_mxn)}** | **{format_number(total_oct_mxn)}** | "
          f"**{format_number(total_growth_mxn)}** | **{total_pct_mxn:.1f}%** | "
          f"**${format_number(total_dec_usd, 2)}** | **${format_number(total_oct_usd, 2)}** | "
          f"**${format_number(total_growth_usd, 2)}** | **{total_pct_usd:.1f}%** |")

    return {
        'dec_mxn': total_dec_mxn,
        'oct_mxn': total_oct_mxn,
        'dec_usd': total_dec_usd,
        'oct_usd': total_oct_usd
    }

def print_combined_table(title, mandates_dec, mandates_oct, mutual_dec, mutual_oct):
    """Print combined mandates + mutual funds table"""
    print(f"\n## {title}")
    print("| Afore | Dec 2024 MXN (M) | Oct 2025 MXN (M) | Growth MXN (M) | Growth % | Dec 2024 USD (M) | Oct 2025 USD (M) | Growth USD (M) | Growth % |")
    print("|-------|----------------:|----------------:|--------------:|---------:|----------------:|----------------:|--------------:|---------:|")

    # Get all Afores
    all_afores = sorted(set(
        list(mandates_dec.keys()) + list(mandates_oct.keys()) +
        list(mutual_dec.keys()) + list(mutual_oct.keys())
    ))

    total_dec_mxn = 0
    total_oct_mxn = 0
    total_dec_usd = 0
    total_oct_usd = 0

    for afore in all_afores:
        # Sum mandates + mutual funds
        dec_mxn = (mandates_dec.get(afore, {}).get('MXN', 0) +
                   mutual_dec.get(afore, {}).get('MXN', 0)) / 1000
        oct_mxn = (mandates_oct.get(afore, {}).get('MXN', 0) +
                   mutual_oct.get(afore, {}).get('MXN', 0)) / 1000
        dec_usd = (mandates_dec.get(afore, {}).get('USD', 0) +
                   mutual_dec.get(afore, {}).get('USD', 0)) / 1_000_000
        oct_usd = (mandates_oct.get(afore, {}).get('USD', 0) +
                   mutual_oct.get(afore, {}).get('USD', 0)) / 1_000_000

        growth_mxn = oct_mxn - dec_mxn
        growth_usd = oct_usd - dec_usd

        pct_mxn = (growth_mxn / dec_mxn * 100) if dec_mxn > 0 else 0
        pct_usd = (growth_usd / dec_usd * 100) if dec_usd > 0 else 0

        total_dec_mxn += dec_mxn
        total_oct_mxn += oct_mxn
        total_dec_usd += dec_usd
        total_oct_usd += oct_usd

        print(f"| {afore} | {format_number(dec_mxn)} | {format_number(oct_mxn)} | "
              f"{format_number(growth_mxn)} | {pct_mxn:.1f}% | "
              f"${format_number(dec_usd, 2)} | ${format_number(oct_usd, 2)} | "
              f"${format_number(growth_usd, 2)} | {pct_usd:.1f}% |")

    # Print totals
    total_growth_mxn = total_oct_mxn - total_dec_mxn
    total_growth_usd = total_oct_usd - total_dec_usd
    total_pct_mxn = (total_growth_mxn / total_dec_mxn * 100) if total_dec_mxn > 0 else 0
    total_pct_usd = (total_growth_usd / total_dec_usd * 100) if total_dec_usd > 0 else 0

    print("|-------|----------------:|----------------:|--------------:|---------:|----------------:|----------------:|--------------:|---------:|")
    print(f"| **TOTAL** | **{format_number(total_dec_mxn)}** | **{format_number(total_oct_mxn)}** | "
          f"**{format_number(total_growth_mxn)}** | **{total_pct_mxn:.1f}%** | "
          f"**${format_number(total_dec_usd, 2)}** | **${format_number(total_oct_usd, 2)}** | "
          f"**${format_number(total_growth_usd, 2)}** | **{total_pct_usd:.1f}%** |")

def print_growth_table(title, dec_data, oct_data, nov_data, currency='USD', show_both_periods=True):
    """Print growth table showing 10-month and 12-month growth"""
    print(f"\n## {title}")

    if show_both_periods:
        print("| Afore | Oct 2025 | 10-Mo Growth | 10-Mo % | 12-Mo Growth | 12-Mo % |")
        print("|-------|----------:|-------------:|--------:|-------------:|--------:|")
    else:
        print("| Afore | Oct 2025 | YTD Growth | YTD % |")
        print("|-------|----------:|-----------:|------:|")

    # Get all Afores
    all_afores = sorted(set(list(dec_data.keys()) + list(oct_data.keys()) + list(nov_data.keys())))

    total_oct = 0
    total_dec = 0
    total_nov = 0

    rows = []

    for afore in all_afores:
        if currency == 'MXN':
            oct_val = oct_data.get(afore, {}).get('MXN', 0) / 1000  # millions
            dec_val = dec_data.get(afore, {}).get('MXN', 0) / 1000
            nov_val = nov_data.get(afore, {}).get('MXN', 0) / 1000
        else:  # USD
            oct_val = oct_data.get(afore, {}).get('USD', 0) / 1_000_000  # millions
            dec_val = dec_data.get(afore, {}).get('USD', 0) / 1_000_000
            nov_val = nov_data.get(afore, {}).get('USD', 0) / 1_000_000

        growth_10mo = oct_val - dec_val
        growth_12mo = oct_val - nov_val

        pct_10mo = (growth_10mo / dec_val * 100) if dec_val > 0 else 0
        pct_12mo = (growth_12mo / nov_val * 100) if nov_val > 0 else 0

        total_oct += oct_val
        total_dec += dec_val
        total_nov += nov_val

        rows.append({
            'afore': afore,
            'oct': oct_val,
            'growth_10mo': growth_10mo,
            'pct_10mo': pct_10mo,
            'growth_12mo': growth_12mo,
            'pct_12mo': pct_12mo
        })

    # Print rows
    prefix = "$" if currency == "USD" else ""
    for row in rows:
        if show_both_periods:
            print(f"| {row['afore']} | {prefix}{format_number(row['oct'], 2)} | "
                  f"{prefix}{format_number(row['growth_10mo'], 2)} | {row['pct_10mo']:.1f}% | "
                  f"{prefix}{format_number(row['growth_12mo'], 2)} | {row['pct_12mo']:.1f}% |")
        else:
            print(f"| {row['afore']} | {prefix}{format_number(row['oct'], 2)} | "
                  f"{prefix}{format_number(row['growth_10mo'], 2)} | {row['pct_10mo']:.1f}% |")

    # Print totals
    total_growth_10mo = total_oct - total_dec
    total_growth_12mo = total_oct - total_nov
    total_pct_10mo = (total_growth_10mo / total_dec * 100) if total_dec > 0 else 0
    total_pct_12mo = (total_growth_12mo / total_nov * 100) if total_nov > 0 else 0

    if show_both_periods:
        print("|-------|----------:|-------------:|--------:|-------------:|--------:|")
        print(f"| **TOTAL** | **{prefix}{format_number(total_oct, 2)}** | "
              f"**{prefix}{format_number(total_growth_10mo, 2)}** | **{total_pct_10mo:.1f}%** | "
              f"**{prefix}{format_number(total_growth_12mo, 2)}** | **{total_pct_12mo:.1f}%** |")
    else:
        print("|-------|----------:|-----------:|------:|")
        print(f"| **TOTAL** | **{prefix}{format_number(total_oct, 2)}** | "
              f"**{prefix}{format_number(total_growth_10mo, 2)}** | **{total_pct_10mo:.1f}%** |")

def main():
    print("Loading data...")
    data = load_data()

    print("Aggregating data by period and concept...")

    # Get data for three periods
    # Nov 2024 (for 12-month comparison)
    nov2024_total = aggregate_by_afore(data, "2024", "11", "Total de Activo")
    nov2024_mandates = aggregate_by_afore(data, "2024", "11", "Inversiones Tercerizadas")
    nov2024_mutual = aggregate_by_afore(data, "2024", "11", "Inversion en Fondos Mutuos")

    # Dec 2024 (for 10-month/YTD comparison)
    dec2024_total = aggregate_by_afore(data, "2024", "12", "Total de Activo")
    dec2024_mandates = aggregate_by_afore(data, "2024", "12", "Inversiones Tercerizadas")
    dec2024_mutual = aggregate_by_afore(data, "2024", "12", "Inversion en Fondos Mutuos")

    # Oct 2025 (current)
    oct2025_total = aggregate_by_afore(data, "2025", "10", "Total de Activo")
    oct2025_mandates = aggregate_by_afore(data, "2025", "10", "Inversiones Tercerizadas")
    oct2025_mutual = aggregate_by_afore(data, "2025", "10", "Inversion en Fondos Mutuos")

    print("\n" + "="*100)
    print("AFORE GROWTH ANALYSIS: YTD (10-Month) and 12-Month Comparison")
    print("Period: November 2024 (12-mo base), December 2024 (10-mo base) → October 2025")
    print("="*100)

    # Print growth tables
    print_growth_table("1. TOTAL ASSETS - MXN (millions)", dec2024_total, oct2025_total, nov2024_total, currency='MXN')
    print_growth_table("2. TOTAL ASSETS - USD (millions)", dec2024_total, oct2025_total, nov2024_total, currency='USD')
    print_growth_table("3. MUTUAL FUNDS - USD (millions)", dec2024_mutual, oct2025_mutual, nov2024_mutual, currency='USD')
    print_growth_table("4. THIRD PARTY MANDATES - USD (millions)", dec2024_mandates, oct2025_mandates, nov2024_mandates, currency='USD')

    print(f"\n**Notes:**")
    print(f"- 10-Month Growth: December 2024 → October 2025 (YTD)")
    print(f"- 12-Month Growth: November 2024 → October 2025")
    print(f"- Exchange Rates: Nov 2024 = 20.0959, Dec 2024 = 20.7862, Oct 2025 = 18.5725 MXN/USD")
    print(f"- All values in millions")

if __name__ == "__main__":
    main()

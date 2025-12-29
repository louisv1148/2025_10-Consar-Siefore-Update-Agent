#!/usr/bin/env python3
"""
Complete Enrichment Pipeline for Latest Month
==============================================
This script:
1. Fetches FX data from Banxico for September 2025
2. Enriches the latest month JSON with FX_EOM and valueUSD
3. Saves the enriched data ready for database integration

Inputs:
- consar_latest_month.json: Latest month data (from extract_latest_month.py)

Outputs:
- consar_latest_month_enriched.json: Complete data with FX and USD values
"""

import requests
import pandas as pd
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# === CONFIG ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_JSON = os.path.join(SCRIPT_DIR, "consar_latest_month.json")
OUTPUT_JSON = os.path.join(SCRIPT_DIR, "consar_latest_month_enriched.json")
BANXICO_API_URL = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF43718/datos"


# Load environment variables
load_dotenv()
BANXICO_TOKEN = os.environ.get("BANXICO_TOKEN")


def fetch_banxico_fx(year, month):
    """
    Fetch end-of-month FX rate for a specific month from Banxico.

    Args:
        year: Year as string (e.g., "2025")
        month: Month as string with zero-padding (e.g., "09")

    Returns:
        Float: End-of-month USD/MXN exchange rate
    """
    print(f"📡 Fetching FX rate for {month}/{year} from Banxico...")

    headers = {"Accept": "application/json"}

    if BANXICO_TOKEN:
        headers["Bmx-Token"] = BANXICO_TOKEN
        print("   ✓ Using Banxico API token")
    else:
        print("   ⚠️  No BANXICO_TOKEN found in environment")
        print("      The API may work without a token for recent data")

    try:
        response = requests.get(BANXICO_API_URL, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            raise ValueError(
                "Authentication failed. Banxico API requires a token.\n"
                "Get your token from: https://www.banxico.org.mx/SieAPIRest/service/v1/token\n"
                "Then set it: export BANXICO_TOKEN='your-token'"
            )
        raise ValueError(f"Error fetching FX data: {e}")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error fetching FX data: {e}")

    try:
        data = response.json()
        series_data = data["bmx"]["series"][0]["datos"]
        print(f"   ✓ Received {len(series_data)} data points from Banxico")
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise ValueError(f"Invalid response from Banxico API: {e}")

    # Convert to DataFrame
    df = pd.DataFrame(series_data)
    df["fecha"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y", errors="coerce")
    df["dato"] = pd.to_numeric(df["dato"], errors="coerce")
    df = df.dropna(subset=["fecha", "dato"])

    # Filter for the target month
    df["year"] = df["fecha"].dt.year.astype(str)
    df["month"] = df["fecha"].dt.month.astype(str).str.zfill(2)

    target_df = df[(df["year"] == year) & (df["month"] == month)]

    if target_df.empty:
        raise ValueError(f"No FX data found for {month}/{year}")

    # Get the last (most recent) rate for the month
    fx_rate = target_df.sort_values("fecha").iloc[-1]["dato"]

    print(f"   ✓ FX rate for {month}/{year}: {fx_rate:.4f} MXN/USD")

    return float(fx_rate)


def enrich_with_fx_and_usd(json_path, fx_rate):
    """
    Enrich the JSON file with FX_EOM and valueUSD.

    Args:
        json_path: Path to the input JSON file
        fx_rate: End-of-month FX rate (MXN/USD)

    Returns:
        List of enriched records
    """
    print(f"\n📊 Enriching data with FX and USD values...")

    # Load data
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"   Loaded {len(data)} records")

    # Enrich each record
    enriched_count = 0
    for record in data:
        # Add FX rate
        record["FX_EOM"] = fx_rate

        # Calculate USD value
        value_mxn = record.get("valueMXN", 0)
        if value_mxn and fx_rate:
            record["valueUSD"] = value_mxn / fx_rate
            enriched_count += 1
        else:
            record["valueUSD"] = 0.0

    print(f"   ✓ Enriched {enriched_count} records with USD values")

    # Calculate statistics
    total_mxn = sum(r.get("valueMXN", 0) for r in data)
    total_usd = sum(r.get("valueUSD", 0) for r in data)

    print(f"\n   Summary:")
    print(f"   • Total MXN: ${total_mxn:,.0f}")
    print(f"   • FX Rate: {fx_rate:.4f} MXN/USD")
    print(f"   • Total USD: ${total_usd:,.0f}")

    return data


def save_enriched_data(data, output_path):
    """
    Save enriched data to JSON file.

    Args:
        data: List of enriched records
        output_path: Path to save the file
    """
    print(f"\n💾 Saving enriched data...")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    file_size = os.path.getsize(output_path) / 1024
    print(f"   ✓ Saved to: {output_path}")
    print(f"   ✓ File size: {file_size:.1f} KB")
    print(f"   ✓ Records: {len(data)}")


def display_sample_records(data, count=5):
    """
    Display sample records to verify enrichment.

    Args:
        data: List of enriched records
        count: Number of records to display
    """
    print(f"\n📋 Sample records (first {count}):")
    print("-" * 120)
    print(f"{'Afore':<15} {'Siefore':<12} {'Concept':<35} {'MXN':>15} {'FX':>8} {'USD':>15}")
    print("-" * 120)

    for record in data[:count]:
        afore = record.get("Afore", "")[:14]
        siefore = record.get("Siefore", "")[:11]
        concept = record.get("Concept", "")[:34]
        mxn = record.get("valueMXN", 0)
        fx = record.get("FX_EOM", 0)
        usd = record.get("valueUSD", 0)

        print(f"{afore:<15} {siefore:<12} {concept:<35} {mxn:>15,.0f} {fx:>8.4f} {usd:>15,.0f}")

    print("-" * 120)


# === MAIN EXECUTION ===
if __name__ == "__main__":
    print("=" * 80)
    print("CONSAR Latest Month Enrichment Pipeline")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    try:
        # Load the source JSON to get the period
        print(f"📂 Loading source data: {SOURCE_JSON}")
        with open(SOURCE_JSON, "r", encoding="utf-8") as f:
            source_data = json.load(f)

        if not source_data:
            raise ValueError("Source JSON file is empty")

        # Get the period from the first record
        first_record = source_data[0]
        target_year = first_record["PeriodYear"]
        target_month = first_record["PeriodMonth"]

        print(f"   ✓ Target period: {target_month}/{target_year}")
        print(f"   ✓ Records: {len(source_data)}")

        # Fetch FX rate from Banxico
        fx_rate = fetch_banxico_fx(target_year, target_month)

        # Enrich data with FX and USD values
        enriched_data = enrich_with_fx_and_usd(SOURCE_JSON, fx_rate)

        # Save enriched data
        save_enriched_data(enriched_data, OUTPUT_JSON)

        # Display sample records
        display_sample_records(enriched_data)

        print(f"\n✅ Enrichment complete!")
        print(f"   Input:  {SOURCE_JSON}")
        print(f"   Output: {OUTPUT_JSON}")
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print(f"   Make sure to run extract_latest_month.py first!")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise

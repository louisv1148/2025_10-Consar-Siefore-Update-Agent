"""
Extract Latest Month Data from CONSAR XLSX Files
-------------------------------------------------
Extracts only the most recent month's data from downloaded Siefore reports
and creates a temporary JSON file for FX enrichment before adding to the
historical database.
"""

import os
import pandas as pd
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup
import requests

# === CONFIG ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_FOLDER = os.path.join(SCRIPT_DIR, "downloaded_files")
OUTPUT_JSON = os.path.join(SCRIPT_DIR, "consar_latest_month.json")
METADATA_FILE = os.path.join(SCRIPT_DIR, "latest_run_metadata.json")
BASE_URL = "https://www.consar.gob.mx/gobmx/aplicativo/siset/Enlace.aspx?md=79"

# Valid AFORE names to filter out junk rows
VALID_AFORES = {
    "Azteca", "Banamex", "Coppel", "Inbursa", "Invercap",
    "PensionISSSTE", "Principal", "Profuturo", "SURA", "XXI Banorte"
}

# Spanish month mapping
MONTHS_ES = {
    "ene": "01", "feb": "02", "mar": "03", "abr": "04",
    "may": "05", "jun": "06", "jul": "07", "ago": "08",
    "sep": "09", "oct": "10", "nov": "11", "dic": "12"
}

# Reverse mapping for display
MONTHS_NUM_TO_ES = {v: k for k, v in MONTHS_ES.items()}

# Filename to Siefore name mapping (based on download order from URL_CONFIGS)
FILENAME_TO_SIEFORE = {
    "Reporte.xlsx": "Pensiones",
    "Reporte (1).xlsx": "60-64",
    "Reporte (2).xlsx": "65-69",
    "Reporte (3).xlsx": "70-74",
    "Reporte (4).xlsx": "75-79",
    "Reporte (5).xlsx": "80-84",
    "Reporte (6).xlsx": "85-89",
    "Reporte (7).xlsx": "90-94",
    "Reporte (8).xlsx": "95-99",
    "Reporte (9).xlsx": "Basica Inicial"
}


def get_latest_period_from_consar():
    """Get the latest available period from CONSAR website."""
    response = requests.get(BASE_URL)
    soup = BeautifulSoup(response.text, "lxml")
    text = soup.get_text()

    # Spanish month abbreviations to numbers
    month_abbrev = {
        'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
    }

    # Look for "Periodo Disponible" pattern like "Ene 19-Sep 25"
    match = re.search(r'Periodo Disponible[^\n]*?(\w{3})\s+(\d{2})-(\w{3})\s+(\d{2})', text, re.IGNORECASE)
    if match:
        end_month_abbr = match.group(3).lower()
        end_year_short = match.group(4)

        month_num = month_abbrev.get(end_month_abbr)
        if month_num:
            year = 2000 + int(end_year_short)
            # Return as strings for comparison with Excel data
            return str(year), f"{month_num:02d}"

    raise ValueError("Could not find 'Periodo Disponible' on the page.")


def parse_spanish_period(period_text):
    """Parse 'ene-2025' style into (year, month)."""
    try:
        text = str(period_text).strip().lower()
        if "-" not in text:
            return None, None
        m, y = text.split("-")
        m = m[:3]  # Handle full words like 'enero'
        return y.strip(), MONTHS_ES.get(m, None)
    except Exception:
        return None, None


def clean_value(val):
    """Convert values to floats, handle commas and N/E."""
    if isinstance(val, str):
        val = val.replace(",", "").strip()
        if val in ["N/E", "N/A", "-", ""]:
            return 0.0
    try:
        return float(val)
    except:
        return 0.0

def detect_units(df):
    """
    Detect the units used in the CONSAR Excel file.
    
    CONSAR specifies units in Row 7 (index 6), typically "Miles de Pesos" (thousands of pesos).
    
    Returns:
        str: The units string (e.g., "Miles de Pesos")
    """
    try:
        # Row 7 (index 6) contains "Unidad: Miles de Pesos"
        units_cell = str(df.iloc[6, 2]).strip()  # Column C (index 2)
        
        print(f"   📏 Detected units: {units_cell}")
        
        # Verify it's the expected format
        if "Miles de Pesos" in units_cell or "miles de pesos" in units_cell.lower():
            print(f"   ✅ Units confirmed: Thousands of Pesos (Miles de Pesos)")
            return "Miles de Pesos"
        elif "Millones" in units_cell or "millones" in units_cell.lower():
            print(f"   ⚠️  WARNING: Units are in MILLIONS, not thousands!")
            return "Millones de Pesos"
        elif "Pesos" in units_cell:
            print(f"   ⚠️  WARNING: Units appear to be in actual PESOS, not thousands!")
            return "Pesos"
        else:
            print(f"   ⚠️  WARNING: Unknown units format: {units_cell}")
            return "Unknown"
    except Exception as e:
        print(f"   ⚠️  Could not detect units: {e}")
        return "Unknown"


def parse_consar_xlsx(filepath, target_year, target_month):
    """
    Parse XLSX file and extract ONLY data for the target year/month.

    Args:
        filepath: Path to the XLSX file
        target_year: Target year as string (e.g., "2025")
        target_month: Target month as string (e.g., "09")
    """
    filename = os.path.basename(filepath)
    print(f"🔍 Parsing: {filename}")
    df = pd.read_excel(filepath, header=None)

    # Detect and verify units
    units = detect_units(df)
    if units not in ["Miles de Pesos"]:
        print(f"   ⚠️  CRITICAL: Expected 'Miles de Pesos' but got '{units}'")
        print(f"   ⚠️  Data may need different conversion factor!")

    # Determine Siefore Name from Header (Row 3, Column 2 -> index 2, 1)
    try:
        header_text = str(df.iloc[2, 1]).strip()
        # Regex to capture name after "Siefore Básica "
        match = re.search(r"Siefore Básica (.*)", header_text, re.IGNORECASE)
        if match:
            siefore_name = match.group(1).strip()
            # Normalize specific names if needed to match historic data
            if siefore_name == "Inicial":
                siefore_name = "Basica Inicial"
        else:
            siefore_name = "Unknown"
            print(f"   ⚠️  Could not extract Siefore name from header: '{header_text}'")
    except Exception as e:
        siefore_name = "Unknown"
        print(f"   ⚠️  Error reading header: {e}")

    print(f"   ✓ Identified Siefore: {siefore_name}")

    # Dates are on row 10 (index 9) when first row is 1
    periods = df.iloc[9, 4:].dropna().tolist()  # columns E onward
    period_pairs = [parse_spanish_period(p) for p in periods if parse_spanish_period(p)[0]]

    # Find the column index for the target month
    target_col_idx = None
    for j, (year, month) in enumerate(period_pairs):
        if year == target_year and month == target_month:
            target_col_idx = 4 + j  # column E onward
            break

    if target_col_idx is None:
        print(f"   ⚠️  Target month {target_month}/{target_year} not found in {siefore_name}")
        return []

    print(f"   ✓ Found target month at column {target_col_idx}")

    records = []
    current_concept = None

    for idx in range(10, len(df)):  # start after header row (row 11 onward)
        concept_candidate = str(df.iloc[idx, 1]).strip()

        # Detect new concept
        if any(keyword in concept_candidate for keyword in ["Activo", "Tercerizadas", "Fiduciarios", "Fondos Mutuos"]):
            current_concept = concept_candidate
            continue

        # Skip empty rows or those without Afore data
        if not current_concept or pd.isna(df.iloc[idx, 1]):
            continue

        afore_name = str(df.iloc[idx, 1]).strip()

        # Skip rows that aren't valid Afore names (footer notes, etc.)
        if afore_name not in VALID_AFORES:
            continue

        # Extract ONLY the target month's value
        value = clean_value(df.iloc[idx, target_col_idx])

        record = {
            "Afore": afore_name,
            "Siefore": siefore_name,
            "Concept": current_concept,
            "PeriodYear": target_year,
            "PeriodMonth": target_month,
            "valueMXN": value,
            "FX_EOM": "",
            "valueUSD": ""
        }
        records.append(record)

    print(f"   ✅ Extracted {len(records)} records for {target_month}/{target_year}")
    return records


# === MAIN EXECUTION ===
if __name__ == "__main__":
    print("🚀 Starting latest month data extraction...\n")

    # Get the latest period from metadata (preferred) or CONSAR (fallback)
    try:
        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, "r") as f:
                meta = json.load(f)
                target_year = meta["year"]
                target_month = meta["month"]
                print(f"📄 Loaded target period from metadata: {target_month}/{target_year}")
        else:
            print("⚠️  Metadata file not found, fetching from CONSAR...")
            target_year, target_month = get_latest_period_from_consar()
            
        month_name = MONTHS_NUM_TO_ES.get(target_month, target_month)
        print(f"📅 Target period: {month_name.upper()}-{target_year}\n")
    except Exception as e:
        print(f"❌ Error getting latest period: {e}")
        exit(1)

    # Process all XLSX files (skip temp files that start with ~$)
    all_records = []
    xlsx_files = [f for f in os.listdir(SOURCE_FOLDER) if f.endswith(".xlsx") and not f.startswith("~$")]

    if not xlsx_files:
        print(f"❌ No XLSX files found in {SOURCE_FOLDER}")
        exit(1)

    print(f"Found {len(xlsx_files)} XLSX files to process\n")

    for file in xlsx_files:
        filepath = os.path.join(SOURCE_FOLDER, file)
        records = parse_consar_xlsx(filepath, target_year, target_month)
        all_records.extend(records)

    # Save to JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Saved {len(all_records)} records to {OUTPUT_JSON}")
    print(f"📊 Period: {month_name.upper()}-{target_year}")
    print(f"📁 Output: {OUTPUT_JSON}")

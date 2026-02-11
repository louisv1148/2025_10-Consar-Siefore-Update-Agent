"""
CONSAR Update Agent
-------------------
Checks if new AUM data is available on CONSAR SISNET,
compares it with your latest GitHub release, and if newer,
downloads all Siefore .xlsx files automatically.
"""

import os
import re
import time
import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

from config import (
    CONSAR_BASE_URL, GITHUB_RELEASES_API, FUND_CONFIGS,
    DOWNLOAD_DIR, METADATA_FILE, MONTHS_ES_TO_INT, retry,
)

# Ensure download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Load GitHub token
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# === SELENIUM SETUP ===
def init_driver():
    """Initialize a headless Chrome WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    return webdriver.Chrome(options=chrome_options)

# === CORE AGENT ===
class ConsarUpdateAgent:
    def __init__(self):
        self.driver = init_driver()
        self.wait = WebDriverWait(self.driver, 15)

    # --- Step 1: Check CONSAR for latest period
    def get_latest_period_from_consar(self):
        response = retry(
            lambda: requests.get(CONSAR_BASE_URL, timeout=30),
            max_attempts=3, delay=5, description="CONSAR fetch"
        )
        soup = BeautifulSoup(response.text, "lxml")
        text = soup.get_text()

        # Look for "Periodo Disponible" pattern like "Ene 19-Sep 25"
        # We want the END date (Sep 25), not the publication date
        match = re.search(r'Periodo Disponible[^\n]*?(\w{3})\s+(\d{2})-(\w{3})\s+(\d{2})', text, re.IGNORECASE)
        if match:
            # Extract the end period (groups 3 and 4)
            end_month_abbr = match.group(3).lower()
            end_year_short = match.group(4)

            month_num = MONTHS_ES_TO_INT.get(end_month_abbr)
            if month_num:
                # Convert 2-digit year to 4-digit (assuming 20xx)
                year = 2000 + int(end_year_short)
                # Use last day of the month as the date
                if month_num in [1, 3, 5, 7, 8, 10, 12]:
                    day = 31
                elif month_num in [4, 6, 9, 11]:
                    day = 30
                else:  # February
                    day = 28

                latest_date = datetime(year, month_num, day)
                print(f"📅 CONSAR latest data period: {latest_date.strftime('%B %Y')}")
                return latest_date

        raise ValueError("Could not find 'Periodo Disponible' on the page.")

    # --- Step 2: Check latest GitHub release
    def get_latest_github_release_date(self):
        headers = {"Accept": "application/vnd.github+json"}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"

        def _fetch():
            resp = requests.get(GITHUB_RELEASES_API, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp

        r = retry(_fetch, max_attempts=3, delay=5, description="GitHub API")
        releases = r.json()
        if not releases:
            raise ValueError("No releases found in the GitHub repository.")

        # Parse date from tag name (format: v2025.08 or 2025.08)
        tag_name = releases[0]["tag_name"]

        # Try to extract YYYY.MM pattern from tag
        match = re.search(r'v?(\d{4})\.(\d{2})', tag_name)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            # Use last day of the month
            if month in [1, 3, 5, 7, 8, 10, 12]:
                day = 31
            elif month in [4, 6, 9, 11]:
                day = 30
            else:  # February
                day = 28
            latest_date = datetime(year, month, day)
            print(f"🗓️  GitHub latest release: {latest_date.strftime('%B %Y')} (tag: {tag_name})")
            return latest_date
        else:
            # Fallback to published_at date if tag doesn't match expected format
            latest_date = datetime.strptime(releases[0]["published_at"].split("T")[0], "%Y-%m-%d")
            print(f"⚠️  Warning: Tag '{tag_name}' doesn't match YYYY.MM format, using publish date")
            print(f"🗓️  GitHub latest release: {latest_date.strftime('%B %Y')}")
            return latest_date

    # --- Step 3: Compare dates
    def check_for_update(self):
        consar_date = self.get_latest_period_from_consar()
        
        # Save metadata for downstream scripts to reuse (avoid double scraping)
        import json
        metadata = {
            "year": str(consar_date.year),
            "month": f"{consar_date.month:02d}"
        }
        with open(METADATA_FILE, "w") as f:
            json.dump(metadata, f)
            
        github_date = self.get_latest_github_release_date()
        if consar_date > github_date:
            print("🟢 New data available on CONSAR!")
            return True
        else:
            print("🔴 No new CONSAR data. Already up to date.")
            return False

    # --- Step 4: Download reports for all funds
    def download_reports(self):
        total = len(FUND_CONFIGS)
        for idx, (cd, config) in enumerate(FUND_CONFIGS.items(), start=1):
            fund_name = config["fund_name"]
            url = f"https://www.consar.gob.mx/gobmx/aplicativo/siset/Series.aspx?cd={cd}&cdAlt=False"

            print(f"\n➡️  Processing {idx}/{total}: {fund_name} (cd={cd})")

            try:
                self.driver.get(url)
                time.sleep(2)

                # Select checkboxes by value
                for checkbox_value in config["checkboxes"]:
                    try:
                        checkbox = self.wait.until(EC.presence_of_element_located(
                            (By.XPATH, f"//input[@type='checkbox' and @value='{checkbox_value}']")
                        ))
                        if not checkbox.is_selected():
                            checkbox.click()
                    except Exception as e:
                        print(f"   ⚠️  Could not find checkbox {checkbox_value}: {e}")

                # Select 'Detalle por Afores' in dropdown
                try:
                    select_element = self.wait.until(EC.presence_of_element_located(
                        (By.XPATH, "//select[contains(@id, 'ddlDetalle')]")
                    ))
                    select_obj = Select(select_element)
                    select_obj.select_by_visible_text('Detalle por Afores')
                    time.sleep(1)
                except Exception as e:
                    print(f"   ⚠️  Could not select 'Detalle por Afores': {e}")

                # Click Export button
                export_button = self.wait.until(EC.element_to_be_clickable(
                    (By.ID, "ctl00_ContentPlaceHolder1_btn_ExportaSeries")
                ))
                export_button.click()
                print(f"   ✓ Export initiated for {fund_name}")
                
                # Smart Wait: Wait for .xls file to appear and stabilize
                # Timeout after 120 seconds
                wait_start = time.time()
                download_success = False
                
                while time.time() - wait_start < 120:
                    files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".xls")]
                    # We expect one new file. Check if any file is growing or recent.
                    # Since we clean the dir before running, we can just check if count == idx
                    if len(files) >= idx:
                        # Found the new file, give it a moment to finish writing
                        time.sleep(2) 
                        download_success = True
                        break
                    time.sleep(1)
                
                if download_success:
                    print(f"   ✅ Download completed")
                else:
                    print(f"   ⚠️  Timeout waiting for download for {fund_name}")

            except Exception as e:
                print(f"   ❌ Error processing {fund_name}: {e}")
                continue

    # --- Step 5: Convert XLS (HTML) files to proper XLSX
    def convert_xls_to_xlsx(self):
        print("\n📊 Converting .xls files to .xlsx format...")
        converted_count = 0
        error_count = 0

        for filename in os.listdir(DOWNLOAD_DIR):
            if filename.endswith(".xls"):
                xls_path = os.path.join(DOWNLOAD_DIR, filename)
                xlsx_path = os.path.splitext(xls_path)[0] + ".xlsx"

                try:
                    # Read HTML table from .xls file
                    tables = pd.read_html(xls_path, encoding='latin1')

                    if not tables:
                        raise ValueError("No tables found in the file.")

                    # Assume the first table is what we need
                    df = tables[0]

                    # Save as proper .xlsx file
                    df.to_excel(xlsx_path, index=False, engine='openpyxl')
                    converted_count += 1
                    print(f"   ✓ Converted: {filename} → {os.path.basename(xlsx_path)}")

                except Exception as e:
                    error_count += 1
                    print(f"   ❌ Error converting {filename}: {e}")

        print(f"\n✅ Conversion complete: {converted_count} files converted, {error_count} errors")

    # --- Step 6: Run full update process
    def run(self):
        try:
            if self.check_for_update():
                print("⬇️ Starting report downloads...")
                
                # Cleanup: Delete existing files to ensure clean state
                print("🧹 Cleaning download directory...")
                for f in os.listdir(DOWNLOAD_DIR):
                    os.remove(os.path.join(DOWNLOAD_DIR, f))
                
                self.download_reports()
                print(f"\n✅ All reports downloaded to: {DOWNLOAD_DIR}")
                self.convert_xls_to_xlsx()
            else:
                print("⏹️  No update needed. Exiting.")
        finally:
            self.driver.quit()


# === MAIN ENTRY ===
def main():
    agent = ConsarUpdateAgent()
    agent.run()


if __name__ == "__main__":
    main()

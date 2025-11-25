"""
Download Basica Inicial Fund Only
----------------------------------
Downloads the missing 10th fund (Basica Inicial) with extended wait time.
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

# === CONFIG ===
DOWNLOAD_DIR = "/Users/lvc/AI Scripts/2025_10 Consar Siefore Update Agent/downloaded_files"
FUND_CD = "246"
FUND_NAME = "Basica Inicial"
CHECKBOXES = ["57978", "58154", "58275", "58308"]

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

# === DOWNLOAD FUNCTION ===
def download_fund():
    url = f"https://www.consar.gob.mx/gobmx/aplicativo/siset/Series.aspx?cd={FUND_CD}&cdAlt=False"

    print(f"🔄 Downloading {FUND_NAME} (cd={FUND_CD})")
    print(f"   URL: {url}")

    driver = init_driver()
    wait = WebDriverWait(driver, 30)  # Increased timeout to 30 seconds

    try:
        driver.get(url)
        print(f"   ✓ Page loaded")
        time.sleep(3)  # Extra wait for page to fully load

        # Select checkboxes
        print(f"   Selecting checkboxes...")
        for checkbox_value in CHECKBOXES:
            try:
                checkbox = wait.until(EC.presence_of_element_located(
                    (By.XPATH, f"//input[@type='checkbox' and @value='{checkbox_value}']")
                ))
                if not checkbox.is_selected():
                    checkbox.click()
                print(f"     ✓ Checkbox {checkbox_value}")
            except Exception as e:
                print(f"     ⚠️  Could not find checkbox {checkbox_value}: {e}")

        # Select 'Detalle por Afores' in dropdown
        print(f"   Selecting 'Detalle por Afores'...")
        try:
            select_element = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//select[contains(@id, 'ddlDetalle')]")
            ))
            select_obj = Select(select_element)
            select_obj.select_by_visible_text('Detalle por Afores')
            time.sleep(2)
            print(f"     ✓ Dropdown selected")
        except Exception as e:
            print(f"     ⚠️  Could not select dropdown: {e}")

        # Click Export button
        print(f"   Clicking Export button...")
        export_button = wait.until(EC.element_to_be_clickable(
            (By.ID, "ctl00_ContentPlaceHolder1_btn_ExportaSeries")
        ))
        export_button.click()
        print(f"   ✓ Export initiated")

        # Wait longer for download to complete (15 seconds instead of 5)
        print(f"   Waiting 15 seconds for download to complete...")
        time.sleep(15)

        print(f"   ✅ Download complete for {FUND_NAME}")

    except Exception as e:
        print(f"   ❌ Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    print("=" * 60)
    print("Downloading Basica Inicial Fund")
    print("=" * 60)
    download_fund()
    print("\n✓ Script complete")
    print("=" * 60)

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
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

# === CONFIGURATION ===
BASE_URL = "https://www.consar.gob.mx/gobmx/aplicativo/siset/Enlace.aspx?md=79"
GITHUB_RELEASES_API = "https://api.github.com/repos/louisv1148/2025_10-Afore-JSON-cleanup/releases"
DOWNLOAD_DIR = "/Users/lvc/AI Scripts/2025_10 Consar Siefore Update Agent/downloaded_files"

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
        response = requests.get(BASE_URL)
        soup = BeautifulSoup(response.text, "lxml")
        text = soup.get_text()
        match = re.search(r"PERIODO DISPONIBLE\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})", text)
        if not match:
            raise ValueError("Could not find 'PERIODO DISPONIBLE' on the page.")
        latest_str = match.group(1)
        latest_date = datetime.strptime(latest_str, "%d/%m/%Y")
        print(f"📅 CONSAR latest period: {latest_date.strftime('%B %Y')}")
        return latest_date

    # --- Step 2: Check latest GitHub release
    def get_latest_github_release_date(self):
        headers = {"Accept": "application/vnd.github+json"}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"
        r = requests.get(GITHUB_RELEASES_API, headers=headers)
        r.raise_for_status()
        releases = r.json()
        if not releases:
            raise ValueError("No releases found in the GitHub repository.")
        latest_date = datetime.strptime(releases[0]["published_at"].split("T")[0], "%Y-%m-%d")
        print(f"🗓️  GitHub latest release: {latest_date.strftime('%B %Y')}")
        return latest_date

    # --- Step 3: Compare dates
    def check_for_update(self):
        consar_date = self.get_latest_period_from_consar()
        github_date = self.get_latest_github_release_date()
        if consar_date > github_date:
            print("🟢 New data available on CONSAR!")
            return True
        else:
            print("🔴 No new CONSAR data. Already up to date.")
            return False

    # --- Step 4: Get Siefore links
    def get_siefore_links(self):
        response = requests.get(BASE_URL)
        soup = BeautifulSoup(response.text, "lxml")
        links = []
        for a in soup.find_all("a", href=True):
            if "Series.aspx?cd=" in a["href"]:
                links.append("https://www.consar.gob.mx/gobmx/aplicativo/siset/" + a["href"])
        print(f"🔗 Found {len(links)} Siefore links.")
        return links

    # --- Step 5: Perform UI actions in each Siefore
    def download_reports(self):
        siefore_links = self.get_siefore_links()
        for idx, link in enumerate(siefore_links, start=1):
            print(f"\n➡️  Processing Siefore {idx}/{len(siefore_links)}: {link}")
            self.driver.get(link)
            time.sleep(2)

            try:
                # Select 'Detalle por Afores'
                select_elem = self.wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//select[contains(@id, 'ddlDetalle')]")))
                Select(select_elem).select_by_visible_text("Detalle por Afores")

                # Check the 4 required concept boxes
                concepts = [
                    "Total de Activo",
                    "Inversiones Tercerizadas",
                    "Inversión en títulos Fiduciarios",
                    "Inversión en Fondos Mutuos"
                ]
                for c in concepts:
                    try:
                        box = self.wait.until(EC.element_to_be_clickable(
                            (By.XPATH, f"//input[contains(@title, '{c}')]")))
                        if not box.is_selected():
                            box.click()
                    except Exception:
                        print(f"⚠️ Could not find checkbox for: {c}")

                # Click the 'Exportar' button
                export_btn = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//input[@type='submit' and contains(@value, 'Exportar')]")))
                export_btn.click()
                time.sleep(5)

            except Exception as e:
                print(f"❌ Error processing {link}: {e}")
                continue

    # --- Step 6: Run full update process
    def run(self):
        if self.check_for_update():
            print("⬇️ Starting report downloads...")
            self.download_reports()
            print(f"\n✅ All reports downloaded to: {DOWNLOAD_DIR}")
        else:
            print("⏹️  No update needed. Exiting.")


# === MAIN ENTRY ===
if __name__ == "__main__":
    agent = ConsarUpdateAgent()
    agent.run()

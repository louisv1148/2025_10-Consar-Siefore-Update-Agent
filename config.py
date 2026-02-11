"""
Shared Configuration for CONSAR Siefore Update Agent
=====================================================
Central place for all constants, paths, and mappings used across scripts.
"""

import os
import time

# === BASE PATHS ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(SCRIPT_DIR, "downloaded_files")
BACKUP_DIR = os.path.join(SCRIPT_DIR, "backups")

# === OUTPUT FILE PATHS ===
METADATA_FILE = os.path.join(SCRIPT_DIR, "latest_run_metadata.json")
LATEST_MONTH_JSON = os.path.join(SCRIPT_DIR, "consar_latest_month.json")
ENRICHED_JSON = os.path.join(SCRIPT_DIR, "consar_latest_month_enriched.json")
APPROVAL_FILE = os.path.join(SCRIPT_DIR, "approval_pending.json")
CONSISTENCY_REPORT = os.path.join(SCRIPT_DIR, "consistency_report.json")

# Master DB: override via env var in CI/CD, default to local sibling directory
HISTORICAL_DB = os.environ.get(
    "MASTER_DB_PATH",
    os.path.join(SCRIPT_DIR, "../2025_10 Afore JSON cleanup/consar_siefores_with_usd.json")
)

# === EXTERNAL URLS ===
CONSAR_BASE_URL = "https://www.consar.gob.mx/gobmx/aplicativo/siset/Enlace.aspx?md=79"
BANXICO_API_URL = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF43718/datos"

# === REPOSITORY INFO ===
REPO_OWNER = "louisv1148"
HISTORY_REPO_NAME = "2025_10-Afore-JSON-cleanup"
AGENT_REPO_NAME = "2025_10-Consar-Siefore-Update-Agent"
GITHUB_RELEASES_API = f"https://api.github.com/repos/{REPO_OWNER}/{HISTORY_REPO_NAME}/releases"

# === MONTH MAPPINGS ===

# Spanish abbreviation -> zero-padded month string
MONTHS_ES = {
    "ene": "01", "feb": "02", "mar": "03", "abr": "04",
    "may": "05", "jun": "06", "jul": "07", "ago": "08",
    "sep": "09", "oct": "10", "nov": "11", "dic": "12"
}

# Spanish abbreviation -> int (for datetime construction)
MONTHS_ES_TO_INT = {k: int(v) for k, v in MONTHS_ES.items()}

# Zero-padded month string -> Spanish abbreviation
MONTHS_NUM_TO_ES = {v: k for k, v in MONTHS_ES.items()}

# Zero-padded month string -> English name
MONTHS_EN = {
    "01": "January", "02": "February", "03": "March", "04": "April",
    "05": "May", "06": "June", "07": "July", "08": "August",
    "09": "September", "10": "October", "11": "November", "12": "December"
}

# === ENTITY LISTS ===
VALID_AFORES = {
    "Azteca", "Banamex", "Coppel", "Inbursa", "Invercap",
    "PensionISSSTE", "Principal", "Profuturo", "SURA", "XXI Banorte"
}

# === FUND CONFIGURATIONS ===
# CONSAR SISNET page IDs -> Selenium checkbox values for each fund
FUND_CONFIGS = {
    "237": {"fund_name": "Pensiones", "checkboxes": ["51840", "52016", "52137", "52170"]},
    "239": {"fund_name": "60-64", "checkboxes": ["53204", "53380", "53501", "53534"]},
    "240": {"fund_name": "65-69", "checkboxes": ["53886", "54062", "54183", "54216"]},
    "241": {"fund_name": "70-74", "checkboxes": ["54568", "54744", "54865", "54898"]},
    "242": {"fund_name": "75-79", "checkboxes": ["55250", "55426", "55547", "55580"]},
    "243": {"fund_name": "80-84", "checkboxes": ["55932", "56108", "56229", "56262"]},
    "244": {"fund_name": "85-89", "checkboxes": ["56614", "56790", "56911", "56944"]},
    "245": {"fund_name": "90-94", "checkboxes": ["57296", "57472", "57593", "57626"]},
    "388": {"fund_name": "95-99", "checkboxes": ["73771", "73947", "74068", "74101"]},
    "246": {"fund_name": "Basica Inicial", "checkboxes": ["57978", "58154", "58275", "58308"]}
}


# === UTILITIES ===
def retry(func, max_attempts=3, delay=5, description="operation"):
    """Retry a function with exponential backoff."""
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts:
                raise
            wait = delay * attempt
            print(f"   ⚠️  {description} failed (attempt {attempt}/{max_attempts}): {e}")
            print(f"   Retrying in {wait}s...")
            time.sleep(wait)

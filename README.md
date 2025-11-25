# CONSAR Siefore Update Agent

An automated agent that monitors CONSAR SISNET for new Siefore (pension fund) data, downloads reports, enriches with FX rates, and manages the complete update workflow including email review and database integration.

## Features

- **Automatic Detection**: Checks CONSAR website for latest data period vs GitHub releases
- **Complete Download**: Downloads all 10 Siefore reports with proper conversion to XLSX
- **FX Enrichment**: Fetches Banxico FX rates and calculates USD values
- **Email Review**: Sends summary email for approval before database integration
- **Safe Integration**: Backs up data and requires approval before updating historical database
- **GitHub Release**: Automated release creation with proper tagging

## Complete Workflow

### Option 1: Run Complete Pipeline (Recommended)

```bash
python3 run_complete_pipeline.py
```

This runs all steps automatically:
1. Download and convert Siefore reports
2. Extract latest month data
3. Enrich with FX and USD values
4. Send review email (if configured)

### Option 2: Run Steps Manually

```bash
# Step 1: Download reports
python3 consar_agent.py

# Step 2: Extract latest month
python3 extract_latest_month.py

# Step 3: Enrich with FX/USD
BANXICO_TOKEN=your_token python3 enrich_latest_month.py

# Step 4: Fix units and integrate into historical database
python3 fix_units_and_integrate.py

# Step 5: Send review email (optional)
python3 send_review_email.py

# Step 6: After review, approve and integrate (if using email workflow)
python3 approve_and_integrate.py
```

## Prerequisites

- Python 3.8+
- Chrome/Chromium browser
- ChromeDriver (compatible with your Chrome version)
- Banxico API token
- GitHub Personal Access Token

## Installation

1. Clone the repository:
```bash
git clone https://github.com/louisv1148/2025_10-Consar-Siefore-Update-Agent.git
cd 2025_10-Consar-Siefore-Update-Agent
```

2. Create virtual environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Set up environment variables in `.env`:
```
GITHUB_TOKEN=your_github_token_here
BANXICO_TOKEN=your_banxico_token_here

# Optional: For email notifications
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
RECIPIENT_EMAIL=review_email@example.com
```

## Configuration

### Core Settings (in scripts)
- `BASE_URL`: CONSAR SISNET URL
- `GITHUB_RELEASES_API`: Your GitHub repository releases API endpoint
- `DOWNLOAD_DIR`: Where to save downloaded files
- `HISTORICAL_DB`: Path to historical database JSON

### Email Settings (environment variables)
- `SENDER_EMAIL`: Email address to send from
- `SENDER_PASSWORD`: App password (for Gmail, generate at accounts.google.com)
- `RECIPIENT_EMAIL`: Email address to receive reviews
- `SMTP_SERVER`: SMTP server (default: smtp.gmail.com)
- `SMTP_PORT`: SMTP port (default: 587)

## How It Works

### 1. Detection & Download
- Scrapes CONSAR website for "PERIODO DISPONIBLE" (latest data period)
- Parses GitHub release tags (format: v2025.08) for latest database period
- If CONSAR has newer data, downloads all 10 Siefore reports
- Converts HTML-disguised XLS files to proper XLSX format

### 2. Extraction
- Automatically detects latest period from CONSAR
- Extracts only the newest month's data from all XLSX files
- Filters out footer notes and invalid rows
- Maps file names to proper Siefore names

### 3. Enrichment
- Fetches end-of-month USD/MXN rate from Banxico API
- Adds FX_EOM to all records
- Calculates valueUSD for all non-zero MXN values

### 4. Review & Approval
- Sends HTML email with:
  - Period and statistics
  - Sample data preview
  - Approval instructions
- Creates `approval_pending.json` status file

### 5. Integration
- Backs up historical database
- Removes existing records for the period (if re-running)
- Appends new enriched data
- Updates approval status

## Project Structure

```
.
├── consar_agent.py                  # Main download & conversion agent
├── extract_latest_month.py          # Extract latest month data
├── enrich_latest_month.py           # FX enrichment
├── send_review_email.py             # Email review notification
├── approve_and_integrate.py         # Approval & database integration
├── run_complete_pipeline.py         # Master orchestrator
├── download_basica_inicial.py       # Fallback for 10th fund
├── requirements.txt                 # Python dependencies
├── .env                             # Environment variables (not tracked)
├── .gitignore                      # Git ignore rules
├── downloaded_files/                # Downloaded XLS/XLSX files (not tracked)
├── backups/                         # Database backups (not tracked)
├── consar_latest_month.json         # Extracted month data
├── consar_latest_month_enriched.json # FX-enriched data
├── approval_pending.json            # Approval status
└── README.md                        # This file
```

## Outputs

### Intermediate Files
- `consar_latest_month.json` - Raw extracted data for latest month
- `consar_latest_month_enriched.json` - FX-enriched data ready for approval
- `approval_pending.json` - Approval status tracking

### Final Outputs
- Updated historical database (configured path)
- Backup of previous database in `backups/`
- New GitHub release (v2025.MM format)

## Important: Units Information

**CRITICAL**: The CONSAR XLSX files contain values in "miles de pesos" (thousands of MXN), but the extraction process reads them as actual numbers. The historical database stores `valueMXN` in thousands of pesos.

### Units Format
- **CONSAR XLSX files**: Values represent thousands of MXN (e.g., 31,319,202 = 31.3 billion pesos)
- **Historical database**: `valueMXN` stored in thousands of pesos (same as XLSX)
- **To display in millions**: Divide `valueMXN` by 1,000,000,000

### Example
```
XLSX value: 31,319,202.02504
Database valueMXN: 31,319,202,025.04 (thousands)
Display: 31,319.20 millions MXN = 31.32 billions MXN
```

The `fix_units_and_integrate.py` script handles this conversion automatically by multiplying extracted values by 1000.

## Troubleshooting

### Missing 10th file (Basica Inicial)
If the 10th fund doesn't download, run:
```bash
python3 download_basica_inicial.py
```

Then manually convert and continue the pipeline.

### Email not sending
Email is optional. Without email configuration, you can still:
1. Review `consar_latest_month_enriched.json` manually
2. Run `python3 approve_and_integrate.py` when ready

### Banxico API authentication
Get your token from: https://www.banxico.org.mx/SieAPIRest/service/v1/token

## License

MIT License

## Author

Louis V

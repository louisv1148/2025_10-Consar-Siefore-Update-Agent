# CONSAR Siefore Update Agent — Monthly Workflow

## What happens automatically

The pipeline runs on the **15th, 16th, and 20th** of each month at 8:00 AM UTC.
It downloads the latest CONSAR data, enriches it with FX rates, and runs consistency checks.

## Your monthly steps

### 1. Review the pipeline results

Go to: **GitHub Actions > Run Consar Pipeline > latest run**

At the bottom of the run page you'll see a summary with:
- Total AUM by Afore (USD millions)
- FX rate used
- Consistency checks (record counts, entity completeness, asset magnitude)

If something looks off, **do not approve**. Investigate first.

### 2. Approve

Go to: **GitHub Actions > Approve Latest Data > Run workflow**

Click the green button (confirm defaults to "yes"). This single workflow:
1. Integrates new data into the historical database
2. Creates a GitHub release (e.g., v2026.02)
3. Pushes updated DB to the history repo
4. Generates MXN and USD PDF reports
5. Emails the reports (if Gmail password is current)
6. Uploads reports as downloadable artifacts

### 3. Get the reports

**Option A — Download from GitHub:**
Go to the completed "Approve Latest Data" run > Artifacts > `afore-reports`

**Option B — Generate locally:**
```bash
cd "2025_10 Consar Siefore Update Agent"
./run_reports.sh
```
This pulls both repos and generates PDFs in `output/`.

## Troubleshooting

### Pipeline says "No new data available"
CONSAR hasn't published the new month yet. Wait a few days and re-trigger manually.

### Email fails with "Username and Password not accepted"
Gmail app password expired. Generate a new one:
1. Go to https://myaccount.google.com/apppasswords
2. Create a new app password
3. Update `SENDER_PASSWORD` in GitHub repo > Settings > Secrets and variables > Actions

### Approve workflow fails
Check the logs. Common causes:
- History repo push fails: PAT_TOKEN may have expired (regenerate at GitHub > Settings > Developer settings > Personal access tokens)
- Report generation fails: usually a Python dependency issue

## Architecture

Two repos:
- **Agent repo** (`2025_10-Consar-Siefore-Update-Agent`): pipeline, approval, report generation — everything
- **History repo** (`2025_10-Afore-JSON-cleanup`): stores the historical database, releases

The `Consar-AUM-analysis` repo is deprecated — report generation now lives in the agent repo under `reports/`.

## Key files

| File | Purpose |
|------|---------|
| `run_complete_pipeline.py` | Orchestrates download, extract, enrich, verify |
| `approve_and_integrate.py` | Merges new data into historical DB |
| `reports/generate_reports.py` | Generates PDF reports |
| `generate_pipeline_summary.py` | Creates the GitHub Actions summary |
| `run_reports.sh` | One-command local report generation |
| `config.py` | Central configuration (paths, repo names, etc.) |

## Database units

The historical DB stores values in **miles de pesos** (thousands of pesos). The report calculator divides by 1,000 to display in millions with an "M" suffix. Multiply by 1,000 to get actual pesos.

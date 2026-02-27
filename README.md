# CONSAR Siefore Agent

Automated pipeline that monitors CONSAR SISNET for new pension fund (Siefore) data, downloads reports, enriches with FX rates, and manages the complete update workflow including database integration and PDF report generation.

## Quick Start

```bash
# Clone and install
git clone https://github.com/louisv1148/consar-siefore-agent.git
cd consar-siefore-agent
python3 -m venv venv && source venv/bin/activate
pip install -e .

# Set up environment variables in .env
GITHUB_TOKEN=your_github_token
BANXICO_TOKEN=your_banxico_token
```

## How It Works

The pipeline runs automatically via GitHub Actions on the 15th, 16th, and 20th of each month. It:

1. **Downloads** all 10 Siefore reports from CONSAR SISNET
2. **Extracts** the latest month's data from XLSX files
3. **Enriches** with end-of-month FX rates from Banxico
4. **Verifies** data consistency against the historical database
5. **Posts a summary** to GitHub Actions for review

After reviewing, you trigger the approval workflow which integrates the data, creates a GitHub release, generates PDF reports, and emails them.

See [WORKFLOW.md](WORKFLOW.md) for the full monthly workflow.

## Running Locally

```bash
# Run the full pipeline
python -m consar.pipeline.run

# Approve and integrate data
python -m consar.approval.integrate

# Create GitHub release
python -m consar.approval.release

# Generate PDF reports
python -m consar.reports.generate

# Or use the convenience script (pulls repos + generates reports)
./scripts/run_reports.sh
```

## Project Structure

```
consar-siefore-agent/
├── pyproject.toml                    # Package config & dependencies
├── consar/                           # Main package
│   ├── config.py                     # Central configuration
│   ├── pipeline/                     # Data acquisition pipeline
│   │   ├── download.py               # CONSAR SISNET scraper (Selenium)
│   │   ├── extract.py                # XLSX parser
│   │   ├── enrich.py                 # Banxico FX enrichment
│   │   ├── verify.py                 # Consistency checks
│   │   ├── summarize.py              # GitHub Actions summary
│   │   └── run.py                    # Pipeline orchestrator
│   ├── approval/                     # Post-review integration
│   │   ├── integrate.py              # DB merge + backup
│   │   └── release.py                # GitHub release creation
│   └── reports/                      # PDF report generation
│       ├── generate.py               # Report orchestrator
│       └── modules/                  # Report components
├── scripts/
│   └── run_reports.sh                # Local report generation
├── .github/workflows/
│   ├── pipeline.yml                  # Scheduled data pipeline
│   └── approve.yml                   # Manual approval workflow
├── WORKFLOW.md                       # Monthly workflow guide
└── UNITS_DOCUMENTATION.md            # Data units reference
```

## Architecture

Two repositories:
- **consar-siefore-agent** (this repo): Pipeline, approval, report generation
- **consar-siefore-history**: Historical database + GitHub releases

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes | GitHub API access |
| `BANXICO_TOKEN` | Yes | Banxico FX rate API |
| `MASTER_DB_PATH` | No | Override historical DB path (used in CI) |
| `SENDER_EMAIL` | No | Gmail address for report emails |
| `SENDER_PASSWORD` | No | Gmail app password |
| `RECIPIENT_EMAILS` | No | Comma-separated email recipients |

## Database Units

The historical DB stores values in **miles de pesos** (thousands of MXN). Reports divide by 1,000 to display in millions with "M" suffix.

## License

MIT

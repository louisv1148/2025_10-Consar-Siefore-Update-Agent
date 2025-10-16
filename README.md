# CONSAR Siefore Update Agent

An automated agent that monitors CONSAR SISNET for new Siefore (pension fund) data, compares it with your latest GitHub releases, and automatically downloads updated `.xlsx` files when new data becomes available.

## Features

- Automatically checks CONSAR website for the latest available data period
- Compares with your GitHub repository's latest release date
- Downloads all Siefore reports if newer data is available
- Automated web scraping and form interaction using Selenium
- Exports data for multiple concepts:
  - Total de Activo
  - Inversiones Tercerizadas
  - Inversión en títulos Fiduciarios
  - Inversión en Fondos Mutuos

## Prerequisites

- Python 3.8+
- Chrome/Chromium browser
- ChromeDriver (compatible with your Chrome version)
- GitHub Personal Access Token (optional, for higher API rate limits)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/louisv1148/2025_10-Consar-Siefore-Update-Agent.git
cd 2025_10-Consar-Siefore-Update-Agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Create a `.env` file in the project root
   - Add your GitHub token:
```
GITHUB_TOKEN=your_github_token_here
```

## Usage

Run the agent:
```bash
python3 consar_agent.py
```

The script will:
1. Check CONSAR for the latest available period
2. Check your GitHub releases for the latest published date
3. If CONSAR has newer data, automatically download all Siefore reports
4. Save files to `downloaded_files/` directory

## Configuration

Edit the following variables in `consar_agent.py` if needed:

- `BASE_URL`: CONSAR SISNET URL
- `GITHUB_RELEASES_API`: Your GitHub repository releases API endpoint
- `DOWNLOAD_DIR`: Where to save downloaded files

## How It Works

1. **Date Comparison**: Scrapes CONSAR website to find "PERIODO DISPONIBLE" date
2. **GitHub Check**: Fetches latest release date from GitHub API
3. **Update Detection**: Compares dates to determine if new data exists
4. **Automated Download**: Uses Selenium to:
   - Navigate to each Siefore page
   - Select "Detalle por Afores"
   - Check required concept boxes
   - Click export button
   - Download `.xlsx` files

## Project Structure

```
.
├── consar_agent.py        # Main script
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not tracked)
├── .gitignore            # Git ignore rules
├── downloaded_files/     # Download directory (not tracked)
└── README.md             # This file
```

## License

MIT License

## Author

Louis V

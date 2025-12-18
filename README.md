# Martinique Weather Dashboard

Extract, process, and visualize weather data from the Météo France API for Martinique (French Caribbean).

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Virtual environment recommended

## Installation

1. **Extract the project**:
   ```bash
   unzip martinique_weather_v1.0_final.zip
   cd martinique_weather
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   # or: venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your Météo France API credentials
   ```

## Configuration

Get API credentials from: https://portail-api.meteofrance.fr/web/en

Edit `.env` with your settings:

```ini
METEO_FRANCE_APP_ID=your_application_id
METEO_FRANCE_API_KEY=your_api_key
```

| Variable | Required | Description |
|----------|----------|-------------|
| METEO_FRANCE_APP_ID | For live data | Your Météo France application ID |
| METEO_FRANCE_API_KEY | For live data | Your Météo France API key |

## Usage

### View All Commands

```bash
python main.py --help
```

### Demo Mode (No API Key Required)

Generate sample data and all visualizations to test the system:

```bash
python main.py demo
python main.py demo --verbose      # Detailed logging
python main.py demo --dry-run      # Preview without generating files
```

### Live Data Extraction

Extract real weather data from Météo France API:

```bash
python main.py extract
python main.py extract --verbose   # Detailed logging
python main.py extract --dry-run   # Preview without API calls
```

### Automated Scheduler

Start automated updates (vigilance every 30 min, full data every 3 hours):

```bash
python main.py schedule            # Continuous scheduler
python main.py schedule --once     # Single update only
```

### System Information

Check configuration and environment:

```bash
python main.py info
```

## Output Files

After running, find outputs in `output/`:

| File | Description |
|------|-------------|
| `data/city_forecasts.csv` | 7-day forecasts for all cities |
| `data/hourly_*.csv` | 48-hour hourly data per city |
| `data/vigilance_alerts.json` | Current alert levels and phenomena |
| `maps/vigilance_map.html` | Interactive alert map |
| `maps/forecast_map.html` | City forecast map with popups |
| `maps/rain_map.html` | Precipitation heatmap |
| `charts/temperature_chart.html` | Multi-city temperature trends |
| `charts/hourly_dashboard_*.html` | Hourly multi-metric dashboard |
| `charts/city_comparison.html` | Side-by-side city metrics |
| `charts/vigilance_gauge.html` | Alert level gauge |

Logs are saved to `logs/` with timestamps.

## Features

**Data Extraction**
- Weather forecasts for 10 major Martinique cities (7-day outlook)
- Hourly forecasts with 48-hour granularity
- Vigilance/alert data with phenomenon breakdown
- Rain forecasts with next-hour precipitation probability

**Interactive Maps (Folium)**
- Vigilance map with color-coded alert overlays
- Forecast map with city markers and weather popups
- Precipitation heatmap

**Charts & Dashboards (Plotly)**
- Multi-city temperature comparison (min/max over 7 days)
- Hourly dashboard with temperature, precipitation, and wind panels
- City comparison bar charts
- Vigilance gauge indicator

**CLI Features**
- Typer-based CLI with rich output
- `--verbose` flag for debug logging
- `--dry-run` flag for preview mode
- File logging with timestamps
- Progress indicators

## Project Structure

```
martinique_weather/
├── main.py                # Entry point - CLI with typer
├── config.py              # Configuration, constants, geographic data
├── utils.py               # Logging setup and helpers
├── weather_extractor.py   # Météo France API data extraction
├── map_generator.py       # Folium interactive map generation
├── chart_generator.py     # Plotly chart/dashboard generation
├── scheduler.py           # Automated update scheduler
├── requirements.txt       # Python dependencies (pinned versions)
├── .env.example           # Environment template
├── .gitignore             # Git ignore patterns
├── Dockerfile             # Docker container build
├── docker-compose.yml     # Docker Compose configuration
├── README.md              # This file
├── PROJECT_STATUS.md      # Development status
├── tests/                 # Unit tests
├── logs/                  # Execution logs (auto-created)
└── output/
    ├── data/              # CSV and JSON data exports
    ├── maps/              # Generated HTML maps
    └── charts/            # Generated HTML charts
```

## Docker Deployment

```bash
docker-compose up -d martinique-weather     # Start scheduler
docker-compose run --rm extract             # Single extraction
docker-compose run --rm demo                # Demo mode
docker-compose logs -f martinique-weather   # View logs
```

## Testing

```bash
pytest tests/ -v                    # Run all tests
pytest tests/ --cov=. --cov-report=html  # With coverage
```

## Troubleshooting

### "ModuleNotFoundError"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "API credentials not found"
```bash
cp .env.example .env
# Edit .env with your Météo France credentials
```

### Check system status
```bash
python main.py info
```

### View detailed logs
```bash
python main.py demo --verbose
```

## How to Request Modifications

Happy to make changes. When requesting modifications:
1. Describe the change and expected behavior
2. Provide sample input/output if applicable
3. Note any urgency or deadlines

Revisions are always free and fast. Message me on Upwork.

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| meteofrance-api | 1.4.0 | Météo France API client |
| folium | 0.20.0 | Interactive maps |
| plotly | 6.5.0 | Charts and dashboards |
| pandas | 2.3.3 | Data processing |
| schedule | 1.2.2 | Task scheduling |
| typer | 0.20.0 | CLI framework |
| rich | 14.2.0 | Rich console output |
| python-dotenv | 1.2.1 | Environment management |

---

**Delivered by**: Vafa Bayat
**Version**: 1.0
**Date**: 2025-12-15

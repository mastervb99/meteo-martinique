#!/usr/bin/env python3
"""
Martinique Weather Dashboard - Main Entry Point

Extract, process, and visualize weather data from Météo France API for Martinique.

Usage:
    python main.py demo           # Generate demo with sample data
    python main.py extract        # Extract live data (requires API key)
    python main.py schedule       # Start automated scheduler
    python main.py info           # Show configuration and system info
    python main.py --help         # Show all commands

Author: Vafa Bayat
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from config import (
    MARTINIQUE, OUTPUT_DIR, DATA_DIR, MAPS_DIR, CHARTS_DIR,
    VIGILANCE_COLORS, PHENOMENON_TYPES
)
from utils import setup_logging, LogContext

app = typer.Typer(
    help="Martinique Weather Dashboard - Météo France API Integration",
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        console.print("[bold]Martinique Weather Dashboard[/bold] v1.0.0")
        raise typer.Exit()


def generate_sample_data(logger) -> dict:
    """Generate realistic sample data for demonstration."""
    import pandas as pd

    cities = MARTINIQUE["major_cities"]
    forecasts = []
    base_date = datetime.now()

    for city in cities:
        for day_offset in range(7):
            forecast_date = base_date + timedelta(days=day_offset)
            base_temp = 28 + random.uniform(-2, 3)

            forecasts.append({
                "city": city["name"],
                "lat": city["lat"],
                "lon": city["lon"],
                "date": forecast_date.strftime("%Y-%m-%d"),
                "temp_min": round(base_temp - 4, 1),
                "temp_max": round(base_temp + 2, 1),
                "humidity": random.randint(70, 95),
                "precipitation": round(random.uniform(0, 15), 1) if random.random() > 0.4 else 0,
                "wind_speed": random.randint(10, 35),
                "wind_direction": random.randint(0, 360),
                "uv_index": random.randint(8, 11),
                "weather_desc": random.choice([
                    "Ensoleillé", "Partiellement nuageux", "Averses éparses",
                    "Nuageux", "Risque d'orages", "Éclaircies"
                ])
            })

    df = pd.DataFrame(forecasts)
    df.to_csv(Path(DATA_DIR) / "city_forecasts.csv", index=False)
    logger.info(f"Generated {len(df)} forecast records")

    # Generate hourly data for all cities
    def normalize_city_name(name):
        """Normalize city name for filename."""
        import unicodedata
        # Remove accents
        name = unicodedata.normalize('NFD', name)
        name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
        # Convert to lowercase and replace spaces with hyphens
        return name.lower().replace(' ', '-')

    for city in cities:
        hourly = []
        city_base_temp = 26 + random.uniform(-1, 2)  # Slight variation per city

        for hour_offset in range(48):
            hour_time = base_date + timedelta(hours=hour_offset)
            # Temperature varies through the day
            temp_variation = 4 * abs((hour_time.hour - 14) / 12 - 1)
            base_temp = city_base_temp + temp_variation

            hourly.append({
                "datetime": hour_time.isoformat(),
                "temperature": round(base_temp + random.uniform(-1, 1), 1),
                "feels_like": round(base_temp + random.uniform(1, 3), 1),
                "humidity": random.randint(70, 95),
                "rain_1h": round(random.uniform(0, 5), 1) if random.random() > 0.7 else 0,
                "rain_prob": random.randint(10, 80),
                "wind_speed": random.randint(10, 30),
                "wind_gust": random.randint(20, 45),
                "wind_direction": random.randint(0, 360),
                "cloud_cover": random.randint(20, 90)
            })

        city_slug = normalize_city_name(city["name"])
        pd.DataFrame(hourly).to_csv(Path(DATA_DIR) / f"hourly_{city_slug}.csv", index=False)
        logger.info(f"Generated hourly data for {city['name']}")

    alerts = {
        "timestamp": datetime.now().isoformat(),
        "domain": "972",
        "max_color": random.choice([1, 1, 1, 2, 2, 3]),
        "phenomenons": [
            {"type": "Wind", "color_code": 1, "color_name": "Green", "level": "No particular vigilance"},
            {"type": "Rain-Flood", "color_code": 2, "color_name": "Yellow", "level": "Be attentive"},
            {"type": "Waves-Submersion", "color_code": 1, "color_name": "Green", "level": "No particular vigilance"}
        ]
    }

    with open(Path(DATA_DIR) / "vigilance_alerts.json", "w") as f:
        json.dump(alerts, f, indent=2)

    logger.info("Sample data generation complete")
    return {"forecasts": len(forecasts), "hourly": len(hourly), "alerts": alerts}


@app.command()
def demo(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without generating files"),
    version: bool = typer.Option(False, "--version", "-V", callback=version_callback, is_eager=True, help="Show version"),
):
    """
    Run demonstration with sample data (no API key required).

    Generates realistic weather data and creates all visualizations
    to showcase the dashboard capabilities.
    """
    log_level = "DEBUG" if verbose else "INFO"
    logger = setup_logging(log_level)

    console.print("\n[bold blue]Martinique Weather Dashboard - Demonstration[/bold blue]")
    console.print("=" * 50)

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No files will be written[/yellow]\n")
        logger.info("Dry run: would generate sample data, maps, and charts")
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating sample data...", total=None)
        sample_stats = generate_sample_data(logger)

        progress.update(task, description="Generating interactive maps...")
        from map_generator import MartiniqueMapGenerator
        map_gen = MartiniqueMapGenerator()
        map_results = map_gen.generate_all_maps()

        progress.update(task, description="Generating charts...")
        from chart_generator import MartiniqueChartGenerator
        chart_gen = MartiniqueChartGenerator()
        chart_results = chart_gen.generate_all_charts()

    console.print("\n[bold green]Demonstration complete![/bold green]")
    console.print(f"\nOutput directory: {OUTPUT_DIR}")

    console.print("\n[bold]Maps:[/bold]")
    for name, path in map_results.items():
        if path and "generated_at" not in name:
            console.print(f"  • {name}: {path}")

    console.print("\n[bold]Charts:[/bold]")
    for name, path in chart_results.items():
        if path and "generated_at" not in name:
            console.print(f"  • {name}: {path}")

    console.print("\n[bold]Data files:[/bold]")
    console.print(f"  • {DATA_DIR}/city_forecasts.csv")
    console.print(f"  • {DATA_DIR}/hourly_fort-de-france.csv")
    console.print(f"  • {DATA_DIR}/vigilance_alerts.json")


@app.command()
def extract(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without making API calls"),
):
    """
    Extract live weather data from Météo France API.

    Requires API credentials in .env file:
    - METEO_FRANCE_APP_ID
    - METEO_FRANCE_API_KEY
    """
    log_level = "DEBUG" if verbose else "INFO"
    logger = setup_logging(log_level)

    console.print("\n[bold blue]Live Data Extraction[/bold blue]")

    if dry_run:
        console.print("[yellow]DRY RUN - Would extract data from Météo France API[/yellow]")
        return

    try:
        from weather_extractor import MartiniqueWeatherExtractor

        with LogContext(logger, "Extracting weather data"):
            extractor = MartiniqueWeatherExtractor()
            results = extractor.extract_all()

        with LogContext(logger, "Generating maps"):
            from map_generator import MartiniqueMapGenerator
            MartiniqueMapGenerator().generate_all_maps()

        with LogContext(logger, "Generating charts"):
            from chart_generator import MartiniqueChartGenerator
            MartiniqueChartGenerator().generate_all_charts()

        console.print("\n[bold green]Extraction complete![/bold green]")

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1)


@app.command()
def schedule(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    once: bool = typer.Option(False, "--once", help="Run once instead of continuous"),
):
    """
    Start automated weather data scheduler.

    Runs updates at configured intervals:
    - Vigilance alerts: every 30 minutes
    - Full weather data: every 3 hours
    """
    log_level = "DEBUG" if verbose else "INFO"
    logger = setup_logging(log_level)

    console.print("\n[bold blue]Weather Data Scheduler[/bold blue]")

    from scheduler import WeatherScheduler

    scheduler = WeatherScheduler()

    if once:
        console.print("Running single update...")
        scheduler.run_once()
    else:
        console.print("Starting continuous scheduler (Ctrl+C to stop)")
        scheduler.run()


@app.command()
def api(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to listen on"),
):
    """
    Start the SMS alerts API server.

    Serves the subscription page and API endpoints for:
    - OTP verification
    - Subscription management
    - Alert testing
    """
    console.print("\n[bold blue]Starting Météo Martinique Alertes SMS API[/bold blue]")
    console.print(f"Server: http://{host}:{port}")
    console.print("Docs: http://{host}:{port}/docs")

    from api import run_server
    run_server(host=host, port=port)


@app.command()
def info():
    """
    Show system information and configuration.

    Useful for debugging environment setup.
    """
    import sys
    import platform
    from config import METEO_FRANCE_APP_ID, METEO_FRANCE_API_KEY, TWILIO_ACCOUNT_SID

    console.print("\n[bold]System Information[/bold]")
    console.print(f"  Python:   {sys.version}")
    console.print(f"  Platform: {platform.platform()}")
    console.print(f"  CWD:      {Path.cwd()}")

    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        console.print(f"  .env:     [green]Found[/green]")
    else:
        console.print(f"  .env:     [yellow]Not found (using defaults)[/yellow]")

    console.print("\n[bold]API Configuration[/bold]")
    if METEO_FRANCE_APP_ID:
        console.print(f"  App ID:   [green]Configured[/green]")
    else:
        console.print(f"  App ID:   [red]Not set[/red]")

    if METEO_FRANCE_API_KEY:
        console.print(f"  API Key:  [green]Configured[/green]")
    else:
        console.print(f"  API Key:  [red]Not set[/red]")

    console.print("\n[bold]SMS Configuration (Twilio)[/bold]")
    if TWILIO_ACCOUNT_SID:
        console.print(f"  Twilio:   [green]Configured[/green]")
    else:
        console.print(f"  Twilio:   [yellow]Not set (SMS disabled)[/yellow]")

    console.print("\n[bold]Output Directories[/bold]")
    console.print(f"  Output:   {OUTPUT_DIR}")
    console.print(f"  Maps:     {MAPS_DIR}")
    console.print(f"  Charts:   {CHARTS_DIR}")
    console.print(f"  Data:     {DATA_DIR}")

    console.print("\n[bold]Martinique Configuration[/bold]")
    console.print(f"  Department: {MARTINIQUE['department_code']}")
    console.print(f"  Cities:     {len(MARTINIQUE['major_cities'])}")


if __name__ == "__main__":
    app()

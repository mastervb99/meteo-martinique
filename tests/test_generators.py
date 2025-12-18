"""Tests for map and chart generator modules."""
import pytest
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from map_generator import MartiniqueMapGenerator
from chart_generator import MartiniqueChartGenerator
from config import MARTINIQUE, MAPS_DIR, CHARTS_DIR, DATA_DIR


@pytest.fixture
def sample_forecast_df():
    """Create sample forecast DataFrame for testing."""
    return pd.DataFrame([
        {"city": "Fort-de-France", "lat": 14.6037, "lon": -61.0579,
         "date": "2024-12-15", "temp_min": 24.0, "temp_max": 30.0,
         "humidity": 80, "precipitation": 5.0, "wind_speed": 20},
        {"city": "Le Lamentin", "lat": 14.6099, "lon": -60.9969,
         "date": "2024-12-15", "temp_min": 25.0, "temp_max": 31.0,
         "humidity": 75, "precipitation": 2.0, "wind_speed": 15},
    ])


@pytest.fixture
def sample_hourly_df():
    """Create sample hourly forecast DataFrame."""
    return pd.DataFrame([
        {"datetime": "2024-12-15T00:00:00", "temperature": 26.0,
         "feels_like": 28.0, "humidity": 80, "rain_1h": 0.0,
         "rain_prob": 20, "wind_speed": 15, "wind_gust": 25,
         "wind_direction": 90, "cloud_cover": 50},
        {"datetime": "2024-12-15T01:00:00", "temperature": 25.5,
         "feels_like": 27.5, "humidity": 82, "rain_1h": 0.5,
         "rain_prob": 40, "wind_speed": 18, "wind_gust": 28,
         "wind_direction": 95, "cloud_cover": 60},
    ])


@pytest.fixture
def sample_alerts():
    """Create sample vigilance alerts."""
    return {
        "timestamp": "2024-12-15T12:00:00",
        "domain": "972",
        "max_color": 2,
        "phenomenons": [
            {"type": "Wind", "color_code": 1, "color_name": "Green", "level": "No particular vigilance"},
            {"type": "Rain-Flood", "color_code": 2, "color_name": "Yellow", "level": "Be attentive"},
        ]
    }


class TestMartiniqueMapGenerator:
    """Tests for map generator."""

    def test_init(self):
        gen = MartiniqueMapGenerator()
        assert gen.center == [MARTINIQUE["center"]["lat"], MARTINIQUE["center"]["lon"]]
        assert len(gen.cities) >= 10

    def test_create_base_map(self):
        gen = MartiniqueMapGenerator()
        m = gen.create_base_map()
        assert m is not None
        assert hasattr(m, 'save')

    def test_generate_vigilance_map(self, sample_alerts):
        gen = MartiniqueMapGenerator()
        output_path = gen.generate_vigilance_map(sample_alerts)
        assert output_path.endswith(".html")
        assert Path(output_path).exists()

    def test_generate_forecast_map(self, sample_forecast_df):
        gen = MartiniqueMapGenerator()
        output_path = gen.generate_forecast_map(sample_forecast_df)
        assert output_path.endswith(".html")
        assert Path(output_path).exists()

    def test_generate_rain_map(self):
        gen = MartiniqueMapGenerator()
        output_path = gen.generate_rain_map()
        assert output_path.endswith(".html")
        assert Path(output_path).exists()

    def test_generate_all_maps(self, sample_alerts):
        # Save sample alerts for the test
        with open(Path(DATA_DIR) / "vigilance_alerts.json", "w") as f:
            json.dump(sample_alerts, f)

        gen = MartiniqueMapGenerator()
        results = gen.generate_all_maps()

        assert "vigilance_map" in results
        assert "forecast_map" in results
        assert "rain_map" in results
        assert "generated_at" in results


class TestMartiniqueChartGenerator:
    """Tests for chart generator."""

    def test_init(self):
        gen = MartiniqueChartGenerator()
        assert len(gen.cities) >= 10
        assert len(gen.color_palette) > 0

    def test_generate_temperature_chart(self, sample_forecast_df):
        # Save sample data
        sample_forecast_df.to_csv(Path(DATA_DIR) / "city_forecasts.csv", index=False)

        gen = MartiniqueChartGenerator()
        output_path = gen.generate_temperature_chart()

        if output_path:
            assert output_path.endswith(".html")
            assert Path(output_path).exists()

    def test_generate_hourly_dashboard(self, sample_hourly_df):
        # Save sample data
        sample_hourly_df.to_csv(Path(DATA_DIR) / "hourly_fort-de-france.csv", index=False)

        gen = MartiniqueChartGenerator()
        output_path = gen.generate_hourly_dashboard("Fort-de-France")

        if output_path:
            assert output_path.endswith(".html")
            assert Path(output_path).exists()

    def test_generate_city_comparison(self, sample_forecast_df):
        sample_forecast_df.to_csv(Path(DATA_DIR) / "city_forecasts.csv", index=False)

        gen = MartiniqueChartGenerator()
        output_path = gen.generate_city_comparison()

        if output_path:
            assert output_path.endswith(".html")
            assert Path(output_path).exists()

    def test_generate_vigilance_gauge(self, sample_alerts):
        with open(Path(DATA_DIR) / "vigilance_alerts.json", "w") as f:
            json.dump(sample_alerts, f)

        gen = MartiniqueChartGenerator()
        output_path = gen.generate_vigilance_gauge()

        assert output_path.endswith(".html")
        assert Path(output_path).exists()

    def test_generate_all_charts(self, sample_forecast_df, sample_hourly_df, sample_alerts):
        # Setup all test data
        sample_forecast_df.to_csv(Path(DATA_DIR) / "city_forecasts.csv", index=False)
        sample_hourly_df.to_csv(Path(DATA_DIR) / "hourly_fort-de-france.csv", index=False)
        with open(Path(DATA_DIR) / "vigilance_alerts.json", "w") as f:
            json.dump(sample_alerts, f)

        gen = MartiniqueChartGenerator()
        results = gen.generate_all_charts()

        assert "temperature_chart" in results
        assert "hourly_dashboard" in results
        assert "city_comparison" in results
        assert "vigilance_gauge" in results
        assert "generated_at" in results

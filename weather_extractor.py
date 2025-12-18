"""Weather data extraction from Météo France API for Martinique.

This module provides the MartiniqueWeatherExtractor class for fetching:
- City forecasts (7-day outlook for 10 major cities)
- Hourly forecasts (48-hour granularity)
- Vigilance alerts (weather warnings)
- Rain forecasts (next-hour precipitation)

Usage:
    extractor = MartiniqueWeatherExtractor()
    results = extractor.extract_all()
"""
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

import pandas as pd
from meteofrance_api import MeteoFranceClient
from meteofrance_api.exceptions import MeteoFranceException

from config import (
    MARTINIQUE, DATA_DIR, METEO_FRANCE_API_KEY,
    VIGILANCE_COLORS, PHENOMENON_TYPES
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


class MartiniqueWeatherExtractor:
    """Extract weather data for Martinique from Météo France API.

    Attributes:
        client: MeteoFranceClient instance for API calls
        domain: Météo France domain identifier for Martinique
        cities: List of major Martinique cities with coordinates
    """

    def __init__(self) -> None:
        """Initialize the extractor with Météo France client."""
        self.client = MeteoFranceClient()
        self.domain: str = MARTINIQUE["domain"]
        self.cities: List[Dict[str, Any]] = MARTINIQUE["major_cities"]

    def _retry_api_call(self, func, *args, **kwargs) -> Any:
        """Execute API call with retry logic.

        Args:
            func: Function to call
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from func or None if all retries fail
        """
        for attempt in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except (MeteoFranceException, Exception) as e:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"API call failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                    time.sleep(RETRY_DELAY_SECONDS * (attempt + 1))
                else:
                    logger.error(f"API call failed after {MAX_RETRIES} attempts: {e}")
                    raise
        return None

    def _get_city_by_name(self, city_name: str) -> Dict[str, Any]:
        """Get city data by name, defaulting to first city if not found."""
        return next((c for c in self.cities if c["name"] == city_name), self.cities[0])

    def get_city_forecasts(self) -> pd.DataFrame:
        """Fetch weather forecasts for all major Martinique cities."""
        forecasts = []

        for city in self.cities:
            try:
                forecast = self.client.get_forecast(
                    latitude=city["lat"],
                    longitude=city["lon"],
                    language="fr"
                )

                if forecast and forecast.daily_forecast:
                    for day in forecast.daily_forecast[:7]:
                        forecasts.append({
                            "city": city["name"],
                            "lat": city["lat"],
                            "lon": city["lon"],
                            "date": day.get("dt", ""),
                            "temp_min": day.get("T", {}).get("min"),
                            "temp_max": day.get("T", {}).get("max"),
                            "humidity": day.get("humidity", {}).get("max"),
                            "precipitation": day.get("precipitation", {}).get("24h"),
                            "weather_icon": day.get("weather12H", {}).get("icon"),
                            "weather_desc": day.get("weather12H", {}).get("desc"),
                            "wind_speed": day.get("wind", {}).get("speed"),
                            "wind_direction": day.get("wind", {}).get("direction"),
                            "uv_index": day.get("uv")
                        })

                logger.info(f"Fetched forecast for {city['name']}")

            except Exception as e:
                logger.warning(f"Failed to fetch forecast for {city['name']}: {e}")

        df = pd.DataFrame(forecasts)
        if not df.empty:
            df.to_csv(Path(DATA_DIR) / "city_forecasts.csv", index=False)
            logger.info(f"Saved {len(df)} forecast records")

        return df

    def get_hourly_forecast(self, city_name: str = "Fort-de-France") -> pd.DataFrame:
        """Get hourly forecast for a specific city.

        Args:
            city_name: Name of the city (default: Fort-de-France)

        Returns:
            DataFrame with 48-hour forecast data
        """
        city = self._get_city_by_name(city_name)

        try:
            forecast = self.client.get_forecast(
                latitude=city["lat"],
                longitude=city["lon"],
                language="fr"
            )

            hourly_data = []
            if forecast and forecast.forecast:
                for hour in forecast.forecast[:48]:
                    hourly_data.append({
                        "datetime": hour.get("dt"),
                        "temperature": hour.get("T", {}).get("value"),
                        "feels_like": hour.get("T", {}).get("windchill"),
                        "humidity": hour.get("humidity"),
                        "rain_1h": hour.get("rain", {}).get("1h", 0),
                        "rain_prob": hour.get("rain", {}).get("prob"),
                        "wind_speed": hour.get("wind", {}).get("speed"),
                        "wind_gust": hour.get("wind", {}).get("gust"),
                        "wind_direction": hour.get("wind", {}).get("direction"),
                        "cloud_cover": hour.get("clouds"),
                        "weather_icon": hour.get("weather", {}).get("icon"),
                        "weather_desc": hour.get("weather", {}).get("desc")
                    })

            df = pd.DataFrame(hourly_data)
            if not df.empty:
                df.to_csv(Path(DATA_DIR) / f"hourly_{city_name.lower().replace(' ', '_')}.csv", index=False)

            return df

        except Exception as e:
            logger.error(f"Failed to fetch hourly forecast: {e}")
            return pd.DataFrame()

    def get_vigilance_alerts(self) -> dict:
        """Fetch current vigilance alerts for Martinique."""
        try:
            phenomenons = self.client.get_warning_current_phenomenons(
                domain=MARTINIQUE["department_code"],
                depth=1,
                with_coastal_bulletin=True
            )

            full_bulletin = self.client.get_warning_full(
                domain=MARTINIQUE["department_code"],
                with_coastal_bulletin=True
            )

            alerts = {
                "timestamp": datetime.now().isoformat(),
                "domain": MARTINIQUE["department_code"],
                "max_color": phenomenons.max_color if phenomenons else 1,
                "phenomenons": [],
                "timelaps": []
            }

            if phenomenons and phenomenons.phenomenons_max_colors:
                for phenomenon_id, color in phenomenons.phenomenons_max_colors.items():
                    alerts["phenomenons"].append({
                        "type": PHENOMENON_TYPES.get(phenomenon_id, f"Unknown ({phenomenon_id})"),
                        "color_code": color,
                        "color_name": VIGILANCE_COLORS.get(color, {}).get("name", "Unknown"),
                        "level": VIGILANCE_COLORS.get(color, {}).get("level", "Unknown")
                    })

            if full_bulletin and hasattr(full_bulletin, 'timelaps'):
                for timelap in (full_bulletin.timelaps or []):
                    alerts["timelaps"].append({
                        "begin_time": timelap.get("begin_time"),
                        "end_time": timelap.get("end_time"),
                        "color_id": timelap.get("color_id")
                    })

            with open(Path(DATA_DIR) / "vigilance_alerts.json", "w") as f:
                json.dump(alerts, f, indent=2, default=str)

            logger.info(f"Vigilance level: {alerts['max_color']} - {VIGILANCE_COLORS.get(alerts['max_color'], {}).get('name')}")
            return alerts

        except Exception as e:
            logger.error(f"Failed to fetch vigilance alerts: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def get_rain_forecast(self, city_name: str = "Fort-de-France") -> Dict[str, Any]:
        """Get next-hour rain forecast for a city.

        Args:
            city_name: Name of the city (default: Fort-de-France)

        Returns:
            Dictionary with rain forecast data
        """
        city = self._get_city_by_name(city_name)

        try:
            rain = self.client.get_rain(
                latitude=city["lat"],
                longitude=city["lon"],
                language="fr"
            )

            rain_data = {
                "city": city_name,
                "timestamp": datetime.now().isoformat(),
                "position": {"lat": city["lat"], "lon": city["lon"]},
                "forecast": []
            }

            if rain and rain.forecast:
                for point in rain.forecast:
                    rain_data["forecast"].append({
                        "time": point.get("dt"),
                        "rain_intensity": point.get("rain"),
                        "description": point.get("desc")
                    })

                rain_data["next_rain_in"] = rain.next_rain_date_locale() if hasattr(rain, 'next_rain_date_locale') else None

            return rain_data

        except Exception as e:
            logger.warning(f"Rain forecast not available for {city_name}: {e}")
            return {"error": str(e), "city": city_name}

    def extract_all(self) -> dict:
        """Run all data extractions and return summary."""
        logger.info("Starting full data extraction for Martinique...")

        results = {
            "timestamp": datetime.now().isoformat(),
            "city_forecasts": None,
            "hourly_forecast": None,
            "vigilance": None,
            "rain_forecast": None
        }

        df_cities = self.get_city_forecasts()
        results["city_forecasts"] = len(df_cities) if not df_cities.empty else 0

        df_hourly = self.get_hourly_forecast("Fort-de-France")
        results["hourly_forecast"] = len(df_hourly) if not df_hourly.empty else 0

        results["vigilance"] = self.get_vigilance_alerts()
        results["rain_forecast"] = self.get_rain_forecast("Fort-de-France")

        with open(Path(DATA_DIR) / "extraction_summary.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info("Data extraction complete")
        return results


if __name__ == "__main__":
    extractor = MartiniqueWeatherExtractor()
    summary = extractor.extract_all()
    print(json.dumps(summary, indent=2, default=str))

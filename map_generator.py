"""Generate weather and vigilance maps for Martinique using Folium."""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import folium
from folium import plugins
import pandas as pd

from config import (
    MARTINIQUE, MAPS_DIR, DATA_DIR,
    VIGILANCE_COLORS, PHENOMENON_TYPES
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MartiniqueMapGenerator:
    """Generate interactive weather maps for Martinique."""

    def __init__(self):
        self.center = [MARTINIQUE["center"]["lat"], MARTINIQUE["center"]["lon"]]
        self.bounds = MARTINIQUE["bounds"]
        self.cities = MARTINIQUE["major_cities"]

    def create_base_map(self, zoom: int = 10) -> folium.Map:
        """Create base Folium map centered on Martinique."""
        m = folium.Map(
            location=self.center,
            zoom_start=zoom,
            tiles=None
        )

        folium.TileLayer(
            tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
            attr="CartoDB",
            name="CartoDB Light"
        ).add_to(m)

        folium.TileLayer(
            tiles="OpenStreetMap",
            name="OpenStreetMap"
        ).add_to(m)

        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri",
            name="Satellite"
        ).add_to(m)

        return m

    def generate_vigilance_map(self, alerts: Optional[dict] = None) -> str:
        """Generate vigilance/alert map for Martinique."""
        m = self.create_base_map(zoom=10)

        if alerts is None:
            alert_file = Path(DATA_DIR) / "vigilance_alerts.json"
            if alert_file.exists():
                with open(alert_file) as f:
                    alerts = json.load(f)
            else:
                alerts = {"max_color": 1, "phenomenons": []}

        max_color = alerts.get("max_color", 1)
        color_info = VIGILANCE_COLORS.get(max_color, VIGILANCE_COLORS[1])

        folium.Rectangle(
            bounds=[
                [self.bounds["south"], self.bounds["west"]],
                [self.bounds["north"], self.bounds["east"]]
            ],
            color=color_info["hex"],
            fill=True,
            fill_color=color_info["hex"],
            fill_opacity=0.2,
            popup=f"Martinique - Vigilance {color_info['name']}"
        ).add_to(m)

        legend_html = f'''
        <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000;
                    background-color: white; padding: 15px; border-radius: 5px;
                    border: 2px solid gray; font-family: Arial;">
            <h4 style="margin: 0 0 10px 0;">Vigilance Météo</h4>
            <p style="margin: 5px 0;"><strong>Niveau actuel:</strong>
               <span style="background-color: {color_info['hex']}; padding: 2px 8px; border-radius: 3px;">
               {color_info['name']}</span></p>
            <p style="margin: 5px 0; font-size: 12px;">{color_info['level']}</p>
            <hr style="margin: 10px 0;">
            <p style="margin: 5px 0; font-size: 11px;">
                Mis à jour: {alerts.get('timestamp', datetime.now().isoformat())[:16]}
            </p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))

        if alerts.get("phenomenons"):
            phenom_html = '<div style="position: fixed; bottom: 50px; right: 50px; z-index: 1000; background-color: white; padding: 15px; border-radius: 5px; border: 2px solid gray; font-family: Arial;">'
            phenom_html += '<h4 style="margin: 0 0 10px 0;">Phénomènes</h4>'

            for phenom in alerts["phenomenons"]:
                phenom_color = VIGILANCE_COLORS.get(phenom["color_code"], {}).get("hex", "#888")
                phenom_html += f'''
                <p style="margin: 3px 0; font-size: 12px;">
                    <span style="display: inline-block; width: 12px; height: 12px;
                                 background-color: {phenom_color}; border-radius: 2px;
                                 margin-right: 5px;"></span>
                    {phenom["type"]}
                </p>
                '''

            phenom_html += '</div>'
            m.get_root().html.add_child(folium.Element(phenom_html))

        for city in self.cities:
            folium.CircleMarker(
                location=[city["lat"], city["lon"]],
                radius=5,
                color="navy",
                fill=True,
                popup=city["name"]
            ).add_to(m)

        folium.LayerControl().add_to(m)

        output_path = Path(MAPS_DIR) / "vigilance_map.html"
        m.save(str(output_path))
        logger.info(f"Vigilance map saved: {output_path}")

        return str(output_path)

    def generate_forecast_map(self, forecast_df: Optional[pd.DataFrame] = None) -> str:
        """Generate weather forecast map with city markers."""
        m = self.create_base_map(zoom=10)

        if forecast_df is None:
            csv_path = Path(DATA_DIR) / "city_forecasts.csv"
            if csv_path.exists():
                forecast_df = pd.read_csv(csv_path)

        if forecast_df is not None and not forecast_df.empty:
            today_df = forecast_df.drop_duplicates(subset=["city"], keep="first")

            for _, row in today_df.iterrows():
                popup_html = f'''
                <div style="font-family: Arial; min-width: 150px;">
                    <h4 style="margin: 0 0 8px 0; color: #333;">{row['city']}</h4>
                    <p style="margin: 4px 0;"><b>🌡️ Temp:</b> {row.get('temp_min', 'N/A')}° - {row.get('temp_max', 'N/A')}°C</p>
                    <p style="margin: 4px 0;"><b>💧 Humidité:</b> {row.get('humidity', 'N/A')}%</p>
                    <p style="margin: 4px 0;"><b>🌧️ Précip:</b> {row.get('precipitation', 0)} mm</p>
                    <p style="margin: 4px 0;"><b>💨 Vent:</b> {row.get('wind_speed', 'N/A')} km/h</p>
                    <p style="margin: 4px 0; font-size: 11px;">{row.get('weather_desc', '')}</p>
                </div>
                '''

                temp_max = row.get('temp_max', 25)
                if temp_max and temp_max > 32:
                    marker_color = "red"
                elif temp_max and temp_max > 28:
                    marker_color = "orange"
                else:
                    marker_color = "blue"

                folium.Marker(
                    location=[row["lat"], row["lon"]],
                    popup=folium.Popup(popup_html, max_width=200),
                    icon=folium.Icon(color=marker_color, icon="cloud")
                ).add_to(m)

        else:
            for city in self.cities:
                folium.Marker(
                    location=[city["lat"], city["lon"]],
                    popup=city["name"],
                    icon=folium.Icon(color="blue", icon="cloud")
                ).add_to(m)

        title_html = '''
        <div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%);
                    z-index: 1000; background-color: white; padding: 10px 20px;
                    border-radius: 5px; border: 2px solid #333; font-family: Arial;">
            <h3 style="margin: 0;">🌤️ Prévisions Météo - Martinique</h3>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))

        folium.LayerControl().add_to(m)

        output_path = Path(MAPS_DIR) / "forecast_map.html"
        m.save(str(output_path))
        logger.info(f"Forecast map saved: {output_path}")

        return str(output_path)

    def generate_rain_map(self) -> str:
        """Generate rain intensity map."""
        m = self.create_base_map(zoom=10)

        rain_file = Path(DATA_DIR) / "rain_forecast.json"
        rain_data = {}
        if rain_file.exists():
            with open(rain_file) as f:
                rain_data = json.load(f)

        plugins.HeatMap(
            data=[[city["lat"], city["lon"], 0.5] for city in self.cities],
            radius=25,
            blur=15,
            gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1: 'red'}
        ).add_to(m)

        title_html = '''
        <div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%);
                    z-index: 1000; background-color: white; padding: 10px 20px;
                    border-radius: 5px; border: 2px solid #333; font-family: Arial;">
            <h3 style="margin: 0;">🌧️ Carte des Précipitations - Martinique</h3>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))

        folium.LayerControl().add_to(m)

        output_path = Path(MAPS_DIR) / "rain_map.html"
        m.save(str(output_path))
        logger.info(f"Rain map saved: {output_path}")

        return str(output_path)

    def generate_all_maps(self) -> dict:
        """Generate all map types."""
        results = {
            "vigilance_map": self.generate_vigilance_map(),
            "forecast_map": self.generate_forecast_map(),
            "rain_map": self.generate_rain_map(),
            "generated_at": datetime.now().isoformat()
        }

        with open(Path(MAPS_DIR) / "map_generation_log.json", "w") as f:
            json.dump(results, f, indent=2)

        return results


if __name__ == "__main__":
    generator = MartiniqueMapGenerator()
    results = generator.generate_all_maps()
    print(json.dumps(results, indent=2))

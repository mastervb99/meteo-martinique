"""Generate weather and vigilance maps for Martinique using Folium."""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import folium
from folium import plugins
import pandas as pd
import requests

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

        # Add custom Martinique topographic background
        static_dir = Path(__file__).parent / "static"
        fond_carte_path = static_dir / "fond-carte.png"

        if fond_carte_path.exists():
            folium.raster_layers.ImageOverlay(
                image=str(fond_carte_path),
                bounds=[
                    [self.bounds["south"], self.bounds["west"]],
                    [self.bounds["north"], self.bounds["east"]]
                ],
                opacity=0.8,
                interactive=True,
                cross_origin=False,
                zindex=1,
                name="Fond de carte Martinique"
            ).add_to(m)

        # Keep other tile layers as options
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
        """Generate modern vigilance/alert map for Martinique (Remi style)."""
        # Create base map with modern styling (no default tiles)
        m = folium.Map(
            location=self.center,
            zoom_start=10,
            tiles=None,
            zoomControl=False,
            scrollWheelZoom=False,
            doubleClickZoom=False,
            dragging=False,
            touchZoom=False,
            boxZoom=False,
            keyboard=False
        )

        # Add modern tile layer
        folium.TileLayer(
            tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
            attr='&copy; OpenStreetMap & CARTO',
            name="Base Map",
            subdomains="abcd",
            maxZoom=19
        ).add_to(m)

        # Load alerts data
        if alerts is None:
            alert_file = Path(DATA_DIR) / "vigilance_alerts.json"
            if alert_file.exists():
                with open(alert_file) as f:
                    alerts = json.load(f)
            else:
                alerts = {"max_color": 1, "phenomenons": []}

        max_color = alerts.get("max_color", 1)
        color_info = VIGILANCE_COLORS.get(max_color, VIGILANCE_COLORS[1])

        # Map vigilance colors to Remi's style colors
        remi_colors = {
            1: {"hex": "#2e7d32", "name": "VERTE"},    # Green
            2: {"hex": "#f9a825", "name": "JAUNE"},    # Yellow
            3: {"hex": "#ef6c00", "name": "ORANGE"},   # Orange
            4: {"hex": "#c62828", "name": "ROUGE"}     # Red
        }

        current_color = remi_colors.get(max_color, remi_colors[1])

        # Add Martinique island with GeoJSON outline
        try:
            import requests
            geojson_url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/regions/martinique/region-martinique.geojson"
            response = requests.get(geojson_url, timeout=10)
            if response.status_code == 200:
                geojson_data = response.json()

                folium.GeoJson(
                    geojson_data,
                    style_function=lambda feature: {
                        'color': current_color["hex"],
                        'weight': 4,
                        'opacity': 1,
                        'fillColor': current_color["hex"],
                        'fillOpacity': 0.40
                    }
                ).add_to(m)
        except:
            # Fallback rectangle
            folium.Rectangle(
                bounds=[
                    [self.bounds["south"], self.bounds["west"]],
                    [self.bounds["north"], self.bounds["east"]]
                ],
                color=current_color["hex"],
                fill=True,
                fillColor=current_color["hex"],
                fillOpacity=0.40,
                weight=4
            ).add_to(m)

        # Modern header with glass effect and colored dot
        header_html = f'''
        <div style="position: absolute; top: 14px; left: 14px; z-index: 1200;
                    display: flex; align-items: center; gap: 10px;
                    padding: 10px 14px; border-radius: 14px;
                    background: rgba(255,255,255,0.78); border: 1px solid rgba(0,0,0,0.08);
                    box-shadow: 0 6px 18px rgba(0,0,0,0.15); backdrop-filter: blur(8px);
                    font-family: system-ui, -apple-system, 'Segoe UI', Roboto, Arial;
                    user-select: none;">
            <div style="width: 14px; height: 14px; border-radius: 50%; border: 2px solid rgba(0,0,0,0.25);
                        background: {current_color["hex"]}; flex-shrink: 0;"></div>
            <span style="font-weight: 800; font-size: 14px; text-decoration: underline;
                          color: {current_color["hex"]};">Vigilance {current_color["name"]}</span>
        </div>
        '''

        # Modern legend with glass effect
        legend_html = '''
        <div style="position: absolute; top: 14px; right: 14px; z-index: 1200;
                    padding: 10px 12px; border-radius: 14px;
                    background: rgba(255,255,255,0.72); border: 1px solid rgba(0,0,0,0.08);
                    box-shadow: 0 6px 18px rgba(0,0,0,0.15); backdrop-filter: blur(8px);
                    font-family: system-ui, -apple-system, 'Segoe UI', Roboto, Arial;
                    user-select: none;">
            <div style="font-size: 11px; font-weight: 800; text-transform: uppercase;
                        letter-spacing: 0.4px; margin-bottom: 8px; color: #111;">Légende</div>
            <div style="display: flex; align-items: center; gap: 8px; font-size: 12px; margin-bottom: 6px; white-space: nowrap;">
                <div style="width: 12px; height: 12px; border-radius: 4px; border: 1px solid rgba(0,0,0,0.25);
                            background: #2e7d32; flex-shrink: 0;"></div>
                <span>Verte</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px; font-size: 12px; margin-bottom: 6px; white-space: nowrap;">
                <div style="width: 12px; height: 12px; border-radius: 4px; border: 1px solid rgba(0,0,0,0.25);
                            background: #f9a825; flex-shrink: 0;"></div>
                <span>Jaune</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px; font-size: 12px; margin-bottom: 6px; white-space: nowrap;">
                <div style="width: 12px; height: 12px; border-radius: 4px; border: 1px solid rgba(0,0,0,0.25);
                            background: #ef6c00; flex-shrink: 0;"></div>
                <span>Orange</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px; font-size: 12px; white-space: nowrap;">
                <div style="width: 12px; height: 12px; border-radius: 4px; border: 1px solid rgba(0,0,0,0.25);
                            background: #c62828; flex-shrink: 0;"></div>
                <span>Rouge</span>
            </div>
        </div>
        '''

        # Animated sea overlay effect
        sea_overlay_html = '''
        <div style="position: absolute; inset: 0; z-index: 150; pointer-events: none;
                    background: radial-gradient(circle at 45% 35%,
                        rgba(147,197,253,0.20) 0%,
                        rgba(59,130,246,0.28) 55%,
                        rgba(29,78,216,0.35) 100%);
                    mix-blend-mode: multiply;
                    animation: seaMove 10s ease-in-out infinite;">
        </div>
        <style>
        @keyframes seaMove {
            0% { transform: translate(0,0); }
            50% { transform: translate(10px,6px); }
            100% { transform: translate(0,0); }
        }
        body {
            margin: 0;
            font-family: system-ui, -apple-system, 'Segoe UI', Roboto, Arial;
            background: #f3f4f6;
        }
        .leaflet-container {
            border-radius: 16px;
        }
        </style>
        '''

        # Add all HTML elements to the map
        m.get_root().html.add_child(folium.Element(header_html))
        m.get_root().html.add_child(folium.Element(legend_html))
        m.get_root().html.add_child(folium.Element(sea_overlay_html))

        output_path = Path(MAPS_DIR) / "vigilance_map.html"
        m.save(str(output_path))
        logger.info(f"Modern vigilance map saved: {output_path}")

        return str(output_path)

    def generate_forecast_map(self, forecast_df: Optional[pd.DataFrame] = None) -> str:
        """Generate weather forecast map in Météo-France style."""
        # Create clean base map with blue ocean background
        m = folium.Map(
            location=self.center,
            zoom_start=10,
            tiles=None
        )

        # Add blue ocean tile layer
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Blue_Base/MapServer/tile/{z}/{y}/{x}",
            attr='Esri',
            name="Blue Ocean",
            maxZoom=19
        ).add_to(m)

        # Add Martinique island in green (Météo-France style)
        try:
            import requests
            geojson_url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/regions/martinique/region-martinique.geojson"
            response = requests.get(geojson_url, timeout=10)
            if response.status_code == 200:
                geojson_data = response.json()

                folium.GeoJson(
                    geojson_data,
                    style_function=lambda feature: {
                        'color': '#4a7c59',        # Dark green border
                        'weight': 2,
                        'opacity': 1,
                        'fillColor': '#7fbc00',    # Bright green fill (Météo-France style)
                        'fillOpacity': 0.8
                    }
                ).add_to(m)
        except:
            # Fallback green rectangle
            folium.Rectangle(
                bounds=[
                    [self.bounds["south"], self.bounds["west"]],
                    [self.bounds["north"], self.bounds["east"]]
                ],
                color='#4a7c59',
                fill=True,
                fillColor='#7fbc00',
                fillOpacity=0.8,
                weight=2
            ).add_to(m)

        # Load forecast data
        if forecast_df is None:
            csv_path = Path(DATA_DIR) / "city_forecasts.csv"
            if csv_path.exists():
                forecast_df = pd.read_csv(csv_path)

        # Define weather icon styles (like Météo-France)
        def get_weather_icon_html(temp, weather_desc="", city_name=""):
            """Create custom weather icon HTML like Météo-France style."""
            # Choose weather icon based on description
            if "nuage" in weather_desc.lower() or "cloud" in weather_desc.lower():
                icon = "☁️"
            elif "pluie" in weather_desc.lower() or "rain" in weather_desc.lower():
                icon = "🌧️"
            elif "orage" in weather_desc.lower() or "storm" in weather_desc.lower():
                icon = "⛈️"
            elif "soleil" in weather_desc.lower() or "sun" in weather_desc.lower():
                icon = "☀️"
            else:
                icon = "⛅"  # Default partly cloudy

            return f'''
            <div style="text-align: center; font-family: Arial, sans-serif;">
                <div style="font-size: 24px; margin-bottom: 2px;">{icon}</div>
                <div style="font-weight: bold; font-size: 16px; color: #333;">{temp}°</div>
            </div>
            '''

        # Add weather markers in Météo-France style
        if forecast_df is not None and not forecast_df.empty:
            today_df = forecast_df.drop_duplicates(subset=["city"], keep="first")

            for _, row in today_df.iterrows():
                temp_display = row.get('temp_max', row.get('temperature', 25))
                weather_desc = row.get('weather_desc', '')
                city_name = row.get('city', '')

                # Create custom HTML marker
                icon_html = get_weather_icon_html(temp_display, weather_desc, city_name)

                folium.Marker(
                    location=[row["lat"], row["lon"]],
                    icon=folium.DivIcon(
                        html=icon_html,
                        icon_size=(60, 60),
                        icon_anchor=(30, 30)
                    ),
                    popup=folium.Popup(f'''
                        <div style="text-align: center; font-family: Arial;">
                            <h4 style="margin: 5px 0; color: #333;">{city_name}</h4>
                            <p style="margin: 2px 0;"><b>{temp_display}°C</b></p>
                            <p style="margin: 2px 0; font-size: 12px;">{weather_desc}</p>
                        </div>
                    ''', max_width=150)
                ).add_to(m)

        else:
            # Default markers for main cities
            default_temps = [25, 27, 26, 24, 23, 22, 25, 26]  # Sample temperatures
            for i, city in enumerate(self.cities):
                temp = default_temps[i % len(default_temps)]
                icon_html = get_weather_icon_html(temp, "", city["name"])

                folium.Marker(
                    location=[city["lat"], city["lon"]],
                    icon=folium.DivIcon(
                        html=icon_html,
                        icon_size=(60, 60),
                        icon_anchor=(30, 30)
                    ),
                    popup=folium.Popup(f'''
                        <div style="text-align: center; font-family: Arial;">
                            <h4 style="margin: 5px 0; color: #333;">{city["name"]}</h4>
                            <p style="margin: 2px 0;"><b>{temp}°C</b></p>
                        </div>
                    ''', max_width=150)
                ).add_to(m)

        # Simple title in Météo-France style
        title_html = '''
        <div style="position: absolute; top: 15px; left: 15px; z-index: 1000;
                    background: rgba(255,255,255,0.9); padding: 8px 15px;
                    border-radius: 8px; border: 1px solid #ddd;
                    font-family: Arial, sans-serif; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h3 style="margin: 0; color: #1e40af; font-size: 16px;">Prévisions Météo - Martinique</h3>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))

        # Add minimal controls
        folium.LayerControl().add_to(m)

        output_path = Path(MAPS_DIR) / "forecast_map.html"
        m.save(str(output_path))
        logger.info(f"Météo-France style forecast map saved: {output_path}")

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

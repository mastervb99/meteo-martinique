"""Generate weather charts and visualizations for Martinique using Plotly."""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import MARTINIQUE, CHARTS_DIR, DATA_DIR, VIGILANCE_COLORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MartiniqueChartGenerator:
    """Generate interactive charts for Martinique weather data."""

    def __init__(self):
        self.cities = MARTINIQUE["major_cities"]
        self.color_palette = px.colors.qualitative.Set2

    def generate_temperature_chart(self, df: Optional[pd.DataFrame] = None) -> str:
        """Generate temperature forecast chart for all cities."""
        if df is None:
            csv_path = Path(DATA_DIR) / "city_forecasts.csv"
            if csv_path.exists():
                df = pd.read_csv(csv_path)
            else:
                logger.warning("No forecast data available")
                return ""

        if df.empty:
            return ""

        fig = go.Figure()

        cities = df["city"].unique()
        for i, city in enumerate(cities):
            city_df = df[df["city"] == city].sort_values("date")

            fig.add_trace(go.Scatter(
                x=city_df["date"],
                y=city_df["temp_max"],
                name=f"{city} (Max)",
                mode="lines+markers",
                line=dict(color=self.color_palette[i % len(self.color_palette)]),
                marker=dict(size=8)
            ))

            fig.add_trace(go.Scatter(
                x=city_df["date"],
                y=city_df["temp_min"],
                name=f"{city} (Min)",
                mode="lines+markers",
                line=dict(color=self.color_palette[i % len(self.color_palette)], dash="dot"),
                marker=dict(size=6)
            ))

        fig.update_layout(
            title=dict(text="Prévisions de Température - Martinique", y=0.98),
            xaxis_title="Date",
            yaxis_title="Température (°C)",
            template="plotly_white",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
            margin=dict(b=120)
        )

        output_path = Path(CHARTS_DIR) / "temperature_chart.html"
        fig.write_html(str(output_path))
        logger.info(f"Temperature chart saved: {output_path}")

        return str(output_path)

    def _normalize_city_name(self, name: str) -> str:
        """Normalize city name for filename (remove accents, lowercase, hyphens)."""
        import unicodedata
        name = unicodedata.normalize('NFD', name)
        name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
        return name.lower().replace(' ', '-')

    def generate_hourly_dashboard(self, city: str = "Fort-de-France") -> str:
        """Generate hourly forecast dashboard with multiple metrics."""
        city_slug = self._normalize_city_name(city)
        csv_path = Path(DATA_DIR) / f"hourly_{city_slug}.csv"

        if not csv_path.exists():
            logger.warning(f"No hourly data for {city} (looking for {csv_path})")
            return ""

        df = pd.read_csv(csv_path)
        if df.empty:
            return ""

        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=("Température", "Précipitations", "Vent"),
            vertical_spacing=0.1,
            shared_xaxes=True
        )

        fig.add_trace(
            go.Scatter(
                x=df["datetime"],
                y=df["temperature"],
                name="Température",
                mode="lines+markers",
                line=dict(color="#FF6B6B", width=2),
                fill="tozeroy",
                fillcolor="rgba(255, 107, 107, 0.1)"
            ),
            row=1, col=1
        )

        if "feels_like" in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df["datetime"],
                    y=df["feels_like"],
                    name="Ressenti",
                    mode="lines",
                    line=dict(color="#FF6B6B", dash="dot")
                ),
                row=1, col=1
            )

        fig.add_trace(
            go.Bar(
                x=df["datetime"],
                y=df["rain_1h"],
                name="Pluie (mm/h)",
                marker_color="#4ECDC4"
            ),
            row=2, col=1
        )

        if "rain_prob" in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df["datetime"],
                    y=df["rain_prob"],
                    name="Prob. pluie (%)",
                    mode="lines",
                    line=dict(color="#45B7D1"),
                    yaxis="y4"
                ),
                row=2, col=1
            )

        fig.add_trace(
            go.Scatter(
                x=df["datetime"],
                y=df["wind_speed"],
                name="Vent (km/h)",
                mode="lines+markers",
                line=dict(color="#96CEB4", width=2)
            ),
            row=3, col=1
        )

        if "wind_gust" in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df["datetime"],
                    y=df["wind_gust"],
                    name="Rafales",
                    mode="lines",
                    line=dict(color="#96CEB4", dash="dot")
                ),
                row=3, col=1
            )

        fig.update_layout(
            title=dict(text=f"Prévisions Horaires - {city}", y=0.98),
            height=800,
            template="plotly_white",
            showlegend=True,
            legend=dict(orientation="h", yanchor="top", y=-0.08, xanchor="center", x=0.5),
            margin=dict(b=80)
        )

        fig.update_yaxes(title_text="°C", row=1, col=1)
        fig.update_yaxes(title_text="mm", row=2, col=1)
        fig.update_yaxes(title_text="km/h", row=3, col=1)

        output_path = Path(CHARTS_DIR) / f"hourly_dashboard_{city_slug}.html"
        fig.write_html(str(output_path))
        logger.info(f"Hourly dashboard saved: {output_path}")

        return str(output_path)

    def generate_city_comparison(self, df: Optional[pd.DataFrame] = None) -> str:
        """Generate city comparison bar chart."""
        if df is None:
            csv_path = Path(DATA_DIR) / "city_forecasts.csv"
            if csv_path.exists():
                df = pd.read_csv(csv_path)
            else:
                return ""

        if df.empty:
            return ""

        today_df = df.drop_duplicates(subset=["city"], keep="first")

        fig = make_subplots(
            rows=1, cols=3,
            subplot_titles=("Température Max", "Humidité", "Précipitations"),
            horizontal_spacing=0.1
        )

        fig.add_trace(
            go.Bar(
                x=today_df["city"],
                y=today_df["temp_max"],
                marker_color="#FF6B6B",
                name="Temp Max"
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Bar(
                x=today_df["city"],
                y=today_df["humidity"],
                marker_color="#4ECDC4",
                name="Humidité"
            ),
            row=1, col=2
        )

        fig.add_trace(
            go.Bar(
                x=today_df["city"],
                y=today_df["precipitation"].fillna(0),
                marker_color="#45B7D1",
                name="Précip"
            ),
            row=1, col=3
        )

        fig.update_layout(
            title="Comparaison des Villes - Martinique",
            height=400,
            template="plotly_white",
            showlegend=False
        )

        fig.update_xaxes(tickangle=45)

        output_path = Path(CHARTS_DIR) / "city_comparison.html"
        fig.write_html(str(output_path))
        logger.info(f"City comparison chart saved: {output_path}")

        return str(output_path)

    def generate_vigilance_gauge(self, alerts: Optional[dict] = None) -> str:
        """Generate vigilance level gauge chart."""
        if alerts is None:
            alert_file = Path(DATA_DIR) / "vigilance_alerts.json"
            if alert_file.exists():
                with open(alert_file) as f:
                    alerts = json.load(f)
            else:
                alerts = {"max_color": 1}

        level = alerts.get("max_color", 1)
        color_info = VIGILANCE_COLORS.get(level, VIGILANCE_COLORS[1])

        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=level,
            title={"text": "Niveau de Vigilance"},
            delta={"reference": 1},
            gauge={
                "axis": {"range": [0, 4], "tickvals": [1, 2, 3, 4],
                        "ticktext": ["Vert", "Jaune", "Orange", "Rouge"]},
                "bar": {"color": color_info["hex"]},
                "steps": [
                    {"range": [0, 1], "color": "#E8F5E9"},
                    {"range": [1, 2], "color": "#FFFDE7"},
                    {"range": [2, 3], "color": "#FFF3E0"},
                    {"range": [3, 4], "color": "#FFEBEE"}
                ],
                "threshold": {
                    "line": {"color": "black", "width": 4},
                    "thickness": 0.75,
                    "value": level
                }
            }
        ))

        fig.update_layout(
            height=300,
            template="plotly_white",
            annotations=[
                dict(
                    text=color_info["level"],
                    x=0.5,
                    y=-0.15,
                    showarrow=False,
                    font=dict(size=14)
                )
            ]
        )

        output_path = Path(CHARTS_DIR) / "vigilance_gauge.html"
        fig.write_html(str(output_path))
        logger.info(f"Vigilance gauge saved: {output_path}")

        return str(output_path)

    def generate_all_charts(self) -> dict:
        """Generate all chart types."""
        results = {
            "temperature_chart": self.generate_temperature_chart(),
            "hourly_dashboard": self.generate_hourly_dashboard(),
            "city_comparison": self.generate_city_comparison(),
            "vigilance_gauge": self.generate_vigilance_gauge(),
            "generated_at": datetime.now().isoformat()
        }

        with open(Path(CHARTS_DIR) / "chart_generation_log.json", "w") as f:
            json.dump(results, f, indent=2)

        return results


if __name__ == "__main__":
    generator = MartiniqueChartGenerator()
    results = generator.generate_all_charts()
    print(json.dumps(results, indent=2))

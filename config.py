"""Configuration for Martinique Weather Application."""
import os
from dotenv import load_dotenv

load_dotenv()

# Météo France API credentials
METEO_FRANCE_APP_ID = os.getenv("METEO_FRANCE_APP_ID", "")
METEO_FRANCE_API_KEY = os.getenv("METEO_FRANCE_API_KEY", "")

# Twilio SMS credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")

# Martinique geographic data
MARTINIQUE = {
    "name": "Martinique",
    "department_code": "972",
    "domain": "martinique",
    "center": {"lat": 14.6415, "lon": -61.0242},
    "bounds": {
        "north": 14.88,
        "south": 14.39,
        "east": -60.81,
        "west": -61.24
    },
    "major_cities": [
        {"name": "Fort-de-France", "lat": 14.6037, "lon": -61.0579},
        {"name": "Le Lamentin", "lat": 14.6099, "lon": -60.9969},
        {"name": "Le Robert", "lat": 14.6778, "lon": -60.9381},
        {"name": "Schoelcher", "lat": 14.6147, "lon": -61.0906},
        {"name": "Sainte-Marie", "lat": 14.7831, "lon": -60.9928},
        {"name": "Le François", "lat": 14.6167, "lon": -60.9000},
        {"name": "Ducos", "lat": 14.5500, "lon": -60.9667},
        {"name": "Trinité", "lat": 14.7383, "lon": -60.9658},
        {"name": "Saint-Joseph", "lat": 14.6667, "lon": -61.0333},
        {"name": "Rivière-Pilote", "lat": 14.4667, "lon": -60.9000}
    ]
}

# Vigilance color codes
VIGILANCE_COLORS = {
    1: {"name": "Green", "hex": "#00FF00", "level": "No particular vigilance"},
    2: {"name": "Yellow", "hex": "#FFFF00", "level": "Be attentive"},
    3: {"name": "Orange", "hex": "#FF8C00", "level": "Be very vigilant"},
    4: {"name": "Red", "hex": "#FF0000", "level": "Absolute vigilance"}
}

# Weather phenomenon types
PHENOMENON_TYPES = {
    1: "Wind",
    2: "Rain-Flood",
    3: "Storm",
    4: "Flood",
    5: "Snow-Ice",
    6: "Heat Wave",
    7: "Cold Wave",
    8: "Avalanche",
    9: "Waves-Submersion"
}

# Output directories
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
MAPS_DIR = os.path.join(OUTPUT_DIR, "maps")
CHARTS_DIR = os.path.join(OUTPUT_DIR, "charts")
DATA_DIR = os.path.join(OUTPUT_DIR, "data")

for dir_path in [OUTPUT_DIR, MAPS_DIR, CHARTS_DIR, DATA_DIR]:
    os.makedirs(dir_path, exist_ok=True)

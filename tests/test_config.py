"""Tests for configuration module."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    MARTINIQUE, VIGILANCE_COLORS, PHENOMENON_TYPES,
    OUTPUT_DIR, MAPS_DIR, CHARTS_DIR, DATA_DIR
)


class TestMartiniqueConfig:
    """Test Martinique geographic configuration."""

    def test_martinique_has_required_keys(self):
        required_keys = ["name", "department_code", "domain", "center", "bounds", "major_cities"]
        for key in required_keys:
            assert key in MARTINIQUE, f"Missing key: {key}"

    def test_martinique_center_coordinates(self):
        center = MARTINIQUE["center"]
        assert "lat" in center
        assert "lon" in center
        assert 14.0 < center["lat"] < 15.0, "Latitude should be around 14.6"
        assert -62.0 < center["lon"] < -60.0, "Longitude should be around -61"

    def test_martinique_bounds(self):
        bounds = MARTINIQUE["bounds"]
        assert bounds["north"] > bounds["south"]
        assert bounds["east"] > bounds["west"]

    def test_martinique_cities_count(self):
        cities = MARTINIQUE["major_cities"]
        assert len(cities) >= 10, "Should have at least 10 major cities"

    def test_martinique_cities_have_coordinates(self):
        for city in MARTINIQUE["major_cities"]:
            assert "name" in city
            assert "lat" in city
            assert "lon" in city
            assert isinstance(city["lat"], (int, float))
            assert isinstance(city["lon"], (int, float))

    def test_department_code(self):
        assert MARTINIQUE["department_code"] == "972"


class TestVigilanceColors:
    """Test vigilance color configuration."""

    def test_all_levels_defined(self):
        for level in [1, 2, 3, 4]:
            assert level in VIGILANCE_COLORS
            assert "name" in VIGILANCE_COLORS[level]
            assert "hex" in VIGILANCE_COLORS[level]
            assert "level" in VIGILANCE_COLORS[level]

    def test_color_names(self):
        assert VIGILANCE_COLORS[1]["name"] == "Green"
        assert VIGILANCE_COLORS[2]["name"] == "Yellow"
        assert VIGILANCE_COLORS[3]["name"] == "Orange"
        assert VIGILANCE_COLORS[4]["name"] == "Red"

    def test_hex_format(self):
        for level, info in VIGILANCE_COLORS.items():
            assert info["hex"].startswith("#")
            assert len(info["hex"]) == 7


class TestPhenomenonTypes:
    """Test phenomenon type configuration."""

    def test_phenomenon_types_defined(self):
        assert len(PHENOMENON_TYPES) >= 9
        assert 1 in PHENOMENON_TYPES  # Wind
        assert 2 in PHENOMENON_TYPES  # Rain-Flood

    def test_phenomenon_names(self):
        assert PHENOMENON_TYPES[1] == "Wind"
        assert PHENOMENON_TYPES[2] == "Rain-Flood"
        assert PHENOMENON_TYPES[3] == "Storm"


class TestOutputDirectories:
    """Test output directory configuration."""

    def test_directories_exist(self):
        assert Path(OUTPUT_DIR).exists()
        assert Path(MAPS_DIR).exists()
        assert Path(CHARTS_DIR).exists()
        assert Path(DATA_DIR).exists()

    def test_directory_hierarchy(self):
        assert MAPS_DIR.startswith(OUTPUT_DIR)
        assert CHARTS_DIR.startswith(OUTPUT_DIR)
        assert DATA_DIR.startswith(OUTPUT_DIR)

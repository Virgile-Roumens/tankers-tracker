"""
Configuration module for Tankers Tracker application.

This module contains all configuration constants, region definitions,
and application settings.
"""

import os
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AIS Stream Configuration
AIS_API_KEY = os.getenv("AIS_API_KEY", "77751d32bae3caa0b20f2d7099f03ef5b836fb4c")
AIS_URL = "wss://stream.aisstream.io/v0/stream"

# Application Settings
MAX_TRACKED_SHIPS = int(os.getenv("MAX_TRACKED_SHIPS", "100"))
UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", "2"))
AUTO_MAP_UPDATE_SECONDS = int(os.getenv("AUTO_MAP_UPDATE_SECONDS", "10"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Ship Type Definitions (IMO codes)
TANKER_TYPES = list(range(70, 90))  # 70-89 are tanker/cargo vessel types

# Regional Bounding Boxes [South-West Corner, North-East Corner]
REGIONS: Dict[str, List[List[float]]] = {
    "persian_gulf": [[22, 48], [30, 60]],
    "singapore_strait": [[0, 100], [6, 106]],
    "suez_canal": [[29, 32], [32, 34]],
    "us_gulf": [[25, -98], [31, -80]],
    "north_sea": [[51, -4], [62, 10]],
    "mediterranean": [[30, -6], [46, 37]],
    "malacca": [[1, 98], [6, 105]],
    "gibraltar": [[35, -6], [37, -5]],
    "panama": [[8, -80], [10, -79]],
}

# Major Oil Ports and Terminals
PORTS: Dict[str, List[Dict]] = {
    "persian_gulf": [
        {"name": "Ras Tanura", "lat": 26.6408, "lon": 50.1735, "country": "🇸🇦 Saudi Arabia"},
        {"name": "Mina Al Ahmadi", "lat": 29.0769, "lon": 48.1631, "country": "🇰🇼 Kuwait"},
        {"name": "Kharg Island", "lat": 29.2603, "lon": 50.3241, "country": "🇮🇷 Iran"},
        {"name": "Jebel Ali", "lat": 25.0118, "lon": 55.0618, "country": "🇦🇪 UAE"},
        {"name": "Fujairah", "lat": 25.1164, "lon": 56.3365, "country": "🇦🇪 UAE"},
        {"name": "Das Island", "lat": 25.1500, "lon": 52.8700, "country": "🇦🇪 UAE"},
        {"name": "Ruwais", "lat": 24.1100, "lon": 52.7300, "country": "🇦🇪 UAE"},
    ],
    "singapore_strait": [
        {"name": "Singapore Port", "lat": 1.2644, "lon": 103.8224, "country": "🇸🇬 Singapore"},
        {"name": "Port Klang", "lat": 2.9922, "lon": 101.3919, "country": "🇲🇾 Malaysia"},
        {"name": "Tanjung Pelepas", "lat": 1.3644, "lon": 103.5478, "country": "🇲🇾 Malaysia"},
    ],
    "suez_canal": [
        {"name": "Port Said", "lat": 31.2653, "lon": 32.3019, "country": "🇪🇬 Egypt"},
        {"name": "Suez Port", "lat": 29.9668, "lon": 32.5498, "country": "🇪🇬 Egypt"},
    ],
    "us_gulf": [
        {"name": "Houston", "lat": 29.7604, "lon": -95.3698, "country": "🇺🇸 USA"},
        {"name": "Corpus Christi", "lat": 27.8006, "lon": -97.3964, "country": "🇺🇸 USA"},
        {"name": "Louisiana Offshore", "lat": 29.0000, "lon": -90.0000, "country": "🇺🇸 USA"},
        {"name": "Port Arthur", "lat": 29.8688, "lon": -93.9300, "country": "🇺🇸 USA"},
    ],
    "north_sea": [
        {"name": "Rotterdam", "lat": 51.9225, "lon": 4.4792, "country": "🇳🇱 Netherlands"},
        {"name": "Antwerp", "lat": 51.2194, "lon": 4.4025, "country": "🇧🇪 Belgium"},
    ],
}

# Map Display Settings
MAP_TILES = "CartoDB positron"
MAP_ZOOM_LEVEL = 7
PORT_MARKER_RADIUS = 8
VESSEL_MARKER_RADIUS = 6

# Ship Type Descriptions
SHIP_TYPE_NAMES = {
    70: "Cargo",
    71: "Cargo - Hazardous A",
    72: "Cargo - Hazardous B",
    73: "Cargo - Hazardous C",
    74: "Cargo - Hazardous D",
    80: "Tanker",
    81: "Tanker - Hazardous A",
    82: "Tanker - Hazardous B",
    83: "Tanker - Hazardous C",
    84: "Tanker - Hazardous D",
}
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
MAX_TRACKED_SHIPS = int(os.getenv("MAX_TRACKED_SHIPS", "500"))  # Increased for more tracking
UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", "5"))  # Update map every N position reports
AUTO_MAP_UPDATE_SECONDS = int(os.getenv("AUTO_MAP_UPDATE_SECONDS", "15"))  # Auto-refresh interval
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Map Auto-Refresh Settings
HTML_AUTO_REFRESH_SECONDS = int(os.getenv("HTML_AUTO_REFRESH_SECONDS", "30"))  # HTML page auto-refresh
ENABLE_AUTO_REFRESH = os.getenv("ENABLE_AUTO_REFRESH", "true").lower() == "true"
PAUSE_ON_USER_ACTIVITY = os.getenv("PAUSE_ON_USER_ACTIVITY", "true").lower() == "true"
USER_ACTIVITY_TIMEOUT = int(os.getenv("USER_ACTIVITY_TIMEOUT", "5"))  # Seconds to detect user inactivity

# Performance Settings
ENABLE_CONCURRENT_PROCESSING = os.getenv("ENABLE_CONCURRENT_PROCESSING", "true").lower() == "true"
MESSAGE_BATCH_SIZE = int(os.getenv("MESSAGE_BATCH_SIZE", "50"))  # Process messages in batches (increased from 10)
USE_DATABASE_CACHE = os.getenv("USE_DATABASE_CACHE", "true").lower() == "true"
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/vessels.db")
DATABASE_BATCH_SIZE = int(os.getenv("DATABASE_BATCH_SIZE", "100"))  # Batch database commits
USE_ASYNC_DATABASE = os.getenv("USE_ASYNC_DATABASE", "true").lower() == "true"  # Use aiosqlite for async I/O

# Worldwide Tracking Mode - ALWAYS ON (no regional fallback)
MAX_TRACKED_SHIPS = int(os.getenv("MAX_TRACKED_SHIPS", "5000"))  # All worldwide vessels

# Ship Type Definitions - now using ShipType enum (see enums/ship_type.py)
# Cargo vessels: IMO codes 70-79
# Tankers: IMO codes 80-89
# Use ShipType enum for type-safe ship classification

# Regional Bounding Boxes [South-West Corner, North-East Corner]
# Strategic tanker chokepoints and major oil shipping routes
REGIONS: Dict[str, List[List[float]]] = {
    # MIDDLE EAST - Major oil export regions
    "persian_gulf": [[23, 47], [31, 61]],  # Full Persian Gulf + Gulf of Oman
    "strait_hormuz": [[24, 54], [27, 58]],  # Critical chokepoint: 20% of global oil
    "red_sea": [[12, 36], [20, 45]],  # Red Sea shipping lane
    "bab_el_mandeb": [[11, 41], [14, 45]],  # Southern Red Sea chokepoint
    
    # SUEZ & MEDITERRANEAN - Europe/Asia route
    "suez_canal": [[29, 32], [32, 35]],  # Suez Canal zone - full canal coverage
    "suez_north": [[30.5, 32], [33, 35]],  # Port Said approach (expanded)
    "suez_south": [[27, 32], [30.5, 35]],  # Gulf of Suez approach (expanded for better coverage)
    "mediterranean_east": [[30, 20], [37, 37]],  # East Med: Egypt to Turkey
    "mediterranean_west": [[35, -6], [44, 10]],  # West Med: Gibraltar to Italy
    "gibraltar": [[35.5, -6], [36.5, -5]],  # Strait of Gibraltar (precise)
    
    # SOUTHEAST ASIA - Critical shipping lanes
    "malacca_strait": [[0.5, 98], [6, 105]],  # Strait of Malacca: 25% of global oil
    "singapore_strait": [[1, 103.5], [1.5, 104.5]],  # Singapore Strait (very precise)
    "sunda_strait": [[-7, 104], [-5, 106]],  # Indonesia: Sumatra-Java passage
    "south_china_sea": [[5, 105], [25, 120]],  # Major tanker route
    
    # AMERICAS - Major import/export regions
    "us_gulf": [[25, -98], [31, -80]],  # US Gulf Coast oil terminals
    "caribbean": [[10, -85], [20, -60]],  # Caribbean oil routes
    "panama_canal": [[8, -80.5], [10, -79]],  # Panama Canal zone
    "venezuela_coast": [[8, -72], [12, -60]],  # Venezuelan oil terminals
    "brazil_coast": [[-10, -42], [0, -32]],  # Brazilian offshore oil
    
    # EUROPE & NORTH SEA - Major consumption region
    "north_sea": [[51, -4], [62, 10]],  # North Sea oil & gas
    "english_channel": [[49, -5], [51.5, 2]],  # English Channel shipping
    "baltic_sea": [[53, 10], [66, 31]],  # Baltic tanker routes
    "norwegian_sea": [[60, -2], [72, 15]],  # Norwegian offshore oil
    
    # AFRICA - Emerging routes
    "west_africa": [[0, -10], [10, 10]],  # West African oil (Nigeria, Angola)
    "cape_good_hope": [[-38, 15], [-30, 25]],  # Cape of Good Hope route
    "east_africa": [[-12, 38], [5, 52]],  # East African coast
    
    # ASIA-PACIFIC - Major consumers
    "japan_coast": [[30, 130], [40, 145]],  # Japanese oil terminals
    "korea_strait": [[32, 125], [36, 132]],  # Korea Strait shipping
    "taiwan_strait": [[22, 117], [26, 122]],  # Taiwan Strait
    "east_china_sea": [[25, 120], [35, 130]],  # East China Sea routes
}

# Major Oil Ports and Terminals (focused on tanker operations)
PORTS: Dict[str, List[Dict]] = {
    # PERSIAN GULF - World's largest oil export region
    "persian_gulf": [
        {"name": "Ras Tanura", "lat": 26.6408, "lon": 50.1735, "country": "🇸🇦 Saudi Arabia"},
        {"name": "Mina Al Ahmadi", "lat": 29.0769, "lon": 48.1631, "country": "🇰🇼 Kuwait"},
        {"name": "Kharg Island", "lat": 29.2603, "lon": 50.3241, "country": "🇮🇷 Iran"},
        {"name": "Jebel Ali", "lat": 25.0118, "lon": 55.0618, "country": "🇦🇪 UAE"},
        {"name": "Fujairah", "lat": 25.1164, "lon": 56.3365, "country": "🇦🇪 UAE"},
        {"name": "Das Island", "lat": 25.1500, "lon": 52.8700, "country": "🇦🇪 UAE"},
        {"name": "Ruwais", "lat": 24.1100, "lon": 52.7300, "country": "🇦🇪 UAE"},
        {"name": "Al Basra", "lat": 29.9667, "lon": 48.7833, "country": "🇮🇶 Iraq"},
        {"name": "Bandar Abbas", "lat": 27.1833, "lon": 56.2667, "country": "🇮🇷 Iran"},
    ],
    "strait_hormuz": [
        {"name": "Fujairah Terminal", "lat": 25.1164, "lon": 56.3365, "country": "🇦🇪 UAE"},
        {"name": "Khor Fakkan", "lat": 25.3333, "lon": 56.35, "country": "🇦🇪 UAE"},
        {"name": "Bandar Abbas", "lat": 27.1833, "lon": 56.2667, "country": "🇮🇷 Iran"},
    ],
    "red_sea": [
        {"name": "Yanbu", "lat": 24.0833, "lon": 38.0667, "country": "🇸🇦 Saudi Arabia"},
        {"name": "Jeddah", "lat": 21.5433, "lon": 39.1728, "country": "🇸🇦 Saudi Arabia"},
        {"name": "Port Sudan", "lat": 19.6167, "lon": 37.2167, "country": "🇸🇩 Sudan"},
    ],
    "bab_el_mandeb": [
        {"name": "Djibouti", "lat": 11.5950, "lon": 43.1481, "country": "🇩🇯 Djibouti"},
        {"name": "Aden", "lat": 12.7855, "lon": 45.0187, "country": "🇾🇪 Yemen"},
    ],
    
    # SUEZ CANAL & MEDITERRANEAN
    "suez_canal": [
        {"name": "Port Said", "lat": 31.2653, "lon": 32.3019, "country": "🇪🇬 Egypt"},
        {"name": "Suez Port", "lat": 29.9668, "lon": 32.5498, "country": "🇪🇬 Egypt"},
    ],
    "suez_north": [
        {"name": "Port Said", "lat": 31.2653, "lon": 32.3019, "country": "🇪🇬 Egypt"},
    ],
    "suez_south": [
        {"name": "Suez Terminal", "lat": 29.9668, "lon": 32.5498, "country": "🇪🇬 Egypt"},
    ],
    "mediterranean_east": [
        {"name": "Alexandria", "lat": 31.2001, "lon": 29.9187, "country": "🇪🇬 Egypt"},
        {"name": "Haifa", "lat": 32.8156, "lon": 34.9892, "country": "🇮🇱 Israel"},
        {"name": "Ceyhan", "lat": 36.9000, "lon": 35.8833, "country": "🇹🇷 Turkey"},
        {"name": "Limassol", "lat": 34.6841, "lon": 33.0422, "country": "🇨🇾 Cyprus"},
    ],
    "mediterranean_west": [
        {"name": "Marseille", "lat": 43.2965, "lon": 5.3698, "country": "🇫🇷 France"},
        {"name": "Genoa", "lat": 44.4056, "lon": 8.9463, "country": "🇮🇹 Italy"},
        {"name": "Barcelona", "lat": 41.3851, "lon": 2.1734, "country": "��🇸 Spain"},
        {"name": "Trieste", "lat": 45.6495, "lon": 13.7768, "country": "🇮� Italy"},
        {"name": "Algeciras", "lat": 36.1408, "lon": -5.4536, "country": "🇪🇸 Spain"},
    ],
    "gibraltar": [
        {"name": "Gibraltar", "lat": 36.1408, "lon": -5.3536, "country": "🇬🇮 Gibraltar"},
        {"name": "Algeciras", "lat": 36.1408, "lon": -5.4536, "country": "🇪🇸 Spain"},
    ],
    
    # SOUTHEAST ASIA - Major tanker routes
    "malacca_strait": [
        {"name": "Port Klang", "lat": 2.9922, "lon": 101.3919, "country": "🇲🇾 Malaysia"},
        {"name": "Penang", "lat": 5.4141, "lon": 100.3288, "country": "🇲🇾 Malaysia"},
        {"name": "Belawan", "lat": 3.7833, "lon": 98.6833, "country": "🇮🇩 Indonesia"},
    ],
    "singapore_strait": [
        {"name": "Singapore", "lat": 1.2644, "lon": 103.8224, "country": "🇸🇬 Singapore"},
        {"name": "Jurong Island", "lat": 1.2661, "lon": 103.6992, "country": "�� Singapore"},
    ],
    "sunda_strait": [
        {"name": "Merak", "lat": -5.9333, "lon": 106.0000, "country": "🇮🇩 Indonesia"},
    ],
    "south_china_sea": [
        {"name": "Hong Kong", "lat": 22.3193, "lon": 114.1694, "country": "�� Hong Kong"},
        {"name": "Shenzhen", "lat": 22.5431, "lon": 114.0579, "country": "🇨🇳 China"},
        {"name": "Manila", "lat": 14.6042, "lon": 120.9822, "country": "�� Philippines"},
    ],
    
    # AMERICAS
    "us_gulf": [
        {"name": "Houston", "lat": 29.7604, "lon": -95.3698, "country": "🇺🇸 USA"},
        {"name": "Corpus Christi", "lat": 27.8006, "lon": -97.3964, "country": "🇺🇸 USA"},
        {"name": "Port Arthur", "lat": 29.8688, "lon": -93.9300, "country": "🇺🇸 USA"},
        {"name": "Louisiana LOOP", "lat": 28.8833, "lon": -90.0333, "country": "🇺🇸 USA"},
        {"name": "Freeport", "lat": 28.9536, "lon": -95.3097, "country": "🇺🇸 USA"},
    ],
    "caribbean": [
        {"name": "Cartagena", "lat": 10.3997, "lon": -75.5144, "country": "🇨🇴 Colombia"},
        {"name": "Aruba", "lat": 12.5211, "lon": -70.0269, "country": "🇦🇼 Aruba"},
        {"name": "Curaçao", "lat": 12.1696, "lon": -68.9900, "country": "🇨🇼 Curaçao"},
        {"name": "Trinidad", "lat": 10.6918, "lon": -61.2225, "country": "🇹🇹 Trinidad"},
    ],
    "panama_canal": [
        {"name": "Balboa", "lat": 8.9500, "lon": -79.5667, "country": "🇵🇦 Panama"},
        {"name": "Cristobal", "lat": 9.3597, "lon": -79.9097, "country": "🇵🇦 Panama"},
    ],
    "venezuela_coast": [
        {"name": "Puerto La Cruz", "lat": 10.2167, "lon": -64.6333, "country": "🇻🇪 Venezuela"},
        {"name": "Maracaibo", "lat": 10.6320, "lon": -71.6411, "country": "�� Venezuela"},
    ],
    "brazil_coast": [
        {"name": "Santos", "lat": -23.9608, "lon": -46.3336, "country": "🇧🇷 Brazil"},
        {"name": "Rio de Janeiro", "lat": -22.9068, "lon": -43.1729, "country": "🇧🇷 Brazil"},
    ],
    
    # EUROPE
    "north_sea": [
        {"name": "Rotterdam", "lat": 51.9225, "lon": 4.4792, "country": "🇳🇱 Netherlands"},
        {"name": "Antwerp", "lat": 51.2194, "lon": 4.4025, "country": "🇧🇪 Belgium"},
        {"name": "Immingham", "lat": 53.6333, "lon": -0.1833, "country": "🇬🇧 UK"},
        {"name": "Wilhelmshaven", "lat": 53.5167, "lon": 8.1333, "country": "🇩🇪 Germany"},
    ],
    "english_channel": [
        {"name": "Le Havre", "lat": 49.4944, "lon": 0.1079, "country": "🇫🇷 France"},
        {"name": "Southampton", "lat": 50.9097, "lon": -1.4044, "country": "🇬🇧 UK"},
    ],
    "baltic_sea": [
        {"name": "Gdansk", "lat": 54.3520, "lon": 18.6466, "country": "🇵🇱 Poland"},
        {"name": "Primorsk", "lat": 60.3667, "lon": 28.6167, "country": "🇷🇺 Russia"},
        {"name": "Tallinn", "lat": 59.4370, "lon": 24.7536, "country": "�� Estonia"},
    ],
    "norwegian_sea": [
        {"name": "Mongstad", "lat": 60.8167, "lon": 5.0333, "country": "🇳🇴 Norway"},
        {"name": "Sture", "lat": 60.7333, "lon": 4.8833, "country": "🇳🇴 Norway"},
    ],
    
    # AFRICA
    "west_africa": [
        {"name": "Lagos", "lat": 6.4531, "lon": 3.3958, "country": "�� Nigeria"},
        {"name": "Bonny Island", "lat": 4.4333, "lon": 7.1667, "country": "🇳🇬 Nigeria"},
        {"name": "Luanda", "lat": -8.8368, "lon": 13.2343, "country": "�� Angola"},
    ],
    "cape_good_hope": [
        {"name": "Cape Town", "lat": -33.9249, "lon": 18.4241, "country": "🇿🇦 South Africa"},
        {"name": "Saldanha Bay", "lat": -33.0117, "lon": 17.9442, "country": "🇿🇦 South Africa"},
    ],
    "east_africa": [
        {"name": "Mombasa", "lat": -4.0435, "lon": 39.6682, "country": "🇰🇪 Kenya"},
        {"name": "Dar es Salaam", "lat": -6.7924, "lon": 39.2083, "country": "🇹🇿 Tanzania"},
    ],
    
    # ASIA-PACIFIC
    "japan_coast": [
        {"name": "Yokohama", "lat": 35.4437, "lon": 139.6380, "country": "�� Japan"},
        {"name": "Chiba", "lat": 35.6073, "lon": 140.1064, "country": "🇯🇵 Japan"},
        {"name": "Nagoya", "lat": 35.1815, "lon": 136.9066, "country": "🇯🇵 Japan"},
    ],
    "korea_strait": [
        {"name": "Busan", "lat": 35.1796, "lon": 129.0756, "country": "�� South Korea"},
        {"name": "Ulsan", "lat": 35.5384, "lon": 129.3114, "country": "🇰🇷 South Korea"},
    ],
    "taiwan_strait": [
        {"name": "Kaohsiung", "lat": 22.6273, "lon": 120.3014, "country": "🇹🇼 Taiwan"},
        {"name": "Taichung", "lat": 24.1477, "lon": 120.6736, "country": "🇹🇼 Taiwan"},
    ],
    "east_china_sea": [
        {"name": "Shanghai", "lat": 31.2304, "lon": 121.4737, "country": "🇨🇳 China"},
        {"name": "Ningbo", "lat": 29.8683, "lon": 121.5440, "country": "🇨🇳 China"},
        {"name": "Qingdao", "lat": 36.0671, "lon": 120.3826, "country": "�� China"},
    ],
}

# Map Display Settings
MAP_TILES = "CartoDB positron"
MAP_ZOOM_LEVEL = 7
PORT_MARKER_RADIUS = 5  # Reduced from 8 for cleaner look
VESSEL_MARKER_RADIUS = 3  # Reduced from 6 for smaller boat icons

# Ship Type Descriptions - now using ShipType enum (see enums/ship_type.py)
# SHIP_TYPE_NAMES removed - use ShipType.display_name property instead
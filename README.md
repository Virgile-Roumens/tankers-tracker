# Tankers & Bulk Carriers Tracker

## Overview
The Tankers & Bulk Carriers Tracker is a Python application designed to track **wet bulk (tanker)** and **dry bulk (bulk carrier)** vessels in real-time using AIS (Automatic Identification System) data. The application visualizes vessel positions on an interactive map, classifies vessels by size class, and provides filtering capabilities.

## Features
- **Real-time tracking** of tanker and bulk carrier vessels via AIS data.
- **Wet bulk tracking** — Tankers (AIS types 80–89), classified by size: VLCC, Suezmax, Aframax, Panamax, MR.
- **Dry bulk tracking** — Bulk carriers (AIS types 70–79), classified by size: Capesize, Panamax, Supramax, Handymax, Handysize.
- **Vessel classification** using DWT (Deadweight Tonnage) when available, with dimension-based heuristics as fallback.
- **Bulk carrier filtering** — Filter dry bulk vessels by class (e.g., only Capesize or Panamax).
- **Scalable tracking** — Automatic sub-region batching to track well beyond 2,000 vessels per region.
- **Interactive map** with color-coded markers by vessel category and size class.
- **REST API** for vessel data, statistics, and filtering.
- Support for **multiple geographical regions**.
- Automatic updates of vessel positions and map refresh.

## Dry Bulk Classification

| Class     | DWT Range            | Length Heuristic |
|-----------|----------------------|------------------|
| Capesize  | 100,000+ DWT        | ≥ 270 m          |
| Panamax   | 65,000–100,000 DWT  | ≥ 225 m          |
| Supramax  | 50,000–65,000 DWT   | ≥ 190 m          |
| Handymax  | 40,000–50,000 DWT   | ≥ 170 m          |
| Handysize | 15,000–40,000 DWT   | ≥ 140 m          |
| Small     | < 15,000 DWT        | < 140 m          |

## Project Structure
```
tankers-tracker
├── src
│   ├── start.py                  # Application entry point.
│   ├── tankers_tracker.py        # Main tracking logic (tankers + bulk carriers).
│   ├── config.py                 # Configuration settings.
│   ├── web_interface.py          # Flask web server and REST API.
│   ├── tankers_map.html          # Interactive map template.
│   ├── test_ship_type.py         # Unit tests for ship type classification.
│   ├── data/
│   │   └── current_region.json   # Persisted region selection.
│   ├── enums/
│   │   ├── __init__.py
│   │   ├── ship_type.py          # AIS ship type codes and category helpers.
│   │   ├── bulk_carrier_class.py # Dry bulk size classification (Capesize, etc.).
│   │   ├── tanker_class.py       # Tanker size classification (VLCC, etc.).
│   │   ├── navigational_status.py
│   │   └── region.py             # Geographical region definitions.
│   ├── models/
│   │   ├── __init__.py
│   │   ├── vessel.py             # Vessel data model with classification logic.
│   │   └── region.py             # Region data model.
│   ├── services/
│   │   ├── __init__.py
│   │   └── ...                   # Region manager, bulk tracking service, etc.
│   └── utils/
│       └── ...                   # Map generator, AIS client, helpers.
├── static/
│   └── styles.css                # CSS styles for the web interface.
├── .gitignore
├── requirements.txt              # Python dependencies.
├── START.bat                     # Windows launch script.
└── README.md
```

## Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd tankers-tracker
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set your AIS API key as an environment variable:
   ```bash
   # Linux / macOS
   export AISSTREAM_API_KEY=your_api_key_here

   # Windows (PowerShell)
   $env:AISSTREAM_API_KEY="your_api_key_here"
   ```

## Usage

### Start the application
```bash
python src/start.py
```
Or on Windows, double-click `START.bat`.

### Open the map
Open the generated map in your web browser to view vessel positions with color-coded markers.

### REST API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/vessels` | GET | All tracked vessels. Supports `?category=`, `?bulk_class=`, `?tanker_class=` query params. |
| `/api/vessels/bulk-carriers` | GET | Bulk carriers only. Supports `?class=Capesize` etc. |
| `/api/vessels/tankers` | GET | Tankers only. |
| `/api/statistics` | GET | Classification breakdown (counts by category and class). |
| `/api/filters` | GET | Available filter options (categories, classes, regions). |
| `/api/region` | POST | Set tracking region. Body: `{"region": "..."}` |
| `/api/refresh` | POST | Force refresh vessel data. |

### Filter Examples
```bash
# Get only Capesize bulk carriers
curl "http://localhost:5000/api/vessels/bulk-carriers?class=Capesize"

# Get only Panamax dry bulk vessels
curl "http://localhost:5000/api/vessels?category=Bulk%20Carrier&bulk_class=Panamax"

# Get classification statistics
curl "http://localhost:5000/api/statistics"
```

## How Scaling Beyond 2,000 Vessels Works
Many AIS APIs limit responses to ~2,000 vessels per query. This application automatically detects when a region approaches that limit and recursively splits the bounding box into smaller sub-regions (up to 4 levels deep = 256 sub-areas). Results are deduplicated by MMSI and merged, allowing tracking of **tens of thousands of vessels** across large regions.

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.
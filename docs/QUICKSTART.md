# Quick Start Guide

## Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd tankers-tracker
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On Linux/Mac:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up API key:**
   - Get a free API key from [aisstream.io](https://aisstream.io)
   - Copy `.env.example` to `.env`
   - Update `AIS_API_KEY` in `.env` file

## Running the Tracker

### Basic Usage

```bash
cd src
python tankers_tracker.py
```

This will:
- Track tankers in the Persian Gulf (default region)
- Open an interactive map in your browser
- Auto-refresh the map every 10 seconds

### Custom Configuration

Edit `src/tankers_tracker.py` to customize:

```python
tracker = TankersTracker(
    selected_region="singapore_strait",  # Change region
    max_tracked_ships=50,                # Track fewer ships
    update_interval=5,                   # Update less frequently
    auto_map_update_seconds=15           # Slower auto-refresh
)
```

### Available Regions

Change `selected_region` to any of these:

- `"persian_gulf"` - Persian Gulf area
- `"singapore_strait"` - Singapore/Malacca
- `"suez_canal"` - Suez Canal
- `"us_gulf"` - Gulf of Mexico
- `"north_sea"` - North Sea
- `"mediterranean"` - Mediterranean Sea

## Using the Map

Once running:

1. **Initial map opens** - Shows ports in the region (blue markers)
2. **Vessels appear** - Red markers show tankers as they're detected
3. **Click markers** - View detailed vessel information
4. **Refresh browser** - See latest positions (map auto-updates every 10s)

### Vessel Information

Click any vessel marker to see:
- Vessel name
- MMSI number
- Ship type (Tanker, Cargo, etc.)
- Current speed and course
- Destination port
- GPS coordinates
- Last update time

## Troubleshooting

### No vessels appearing

- **Wait 1-2 minutes** - Ships broadcast every few seconds to minutes
- **Try a busier region** - `singapore_strait` usually has more traffic
- **Check API key** - Verify your `.env` file has the correct key
- **Check console output** - Look for connection messages

### Connection errors

- **Check internet** - WebSocket requires stable connection
- **Try again** - App auto-reconnects after 5 seconds
- **Verify API key** - Make sure it's valid at aisstream.io

### Map not updating

- **Manually refresh** - Browser may cache the map
- **Check terminal** - Look for "Updating map" messages
- **Restart tracker** - Stop (Ctrl+C) and start again

## Next Steps

- **Run tests:** `pytest tests/`
- **Check API docs:** See `docs/API.md`
- **Customize regions:** Edit `src/config.py`
- **Add features:** See `CONTRIBUTING.md`

## Stopping the Tracker

Press `Ctrl+C` to stop. The tracker will:
- Save a final map with all tracked vessels
- Show summary statistics
- Clean up connections

## Advanced Usage

### Programmatic Usage

```python
from tankers_tracker import TankersTracker

# Create tracker
tracker = TankersTracker(selected_region="persian_gulf")

# Start tracking (blocks until Ctrl+C)
try:
    tracker.start()
except KeyboardInterrupt:
    tracker.stop()
```

### Custom Callbacks

```python
from utils.ais_client import AISClient

def my_callback(vessel):
    print(f"New vessel: {vessel.name} at {vessel.lat}, {vessel.lon}")

client = AISClient(
    region_bounds=[[22, 48], [30, 60]],
    on_position_update=my_callback
)
```

See `docs/API.md` for full API documentation.

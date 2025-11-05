# API Documentation

## Classes

### TankersTracker

Main application class for tracking vessels.

**Methods:**

- `__init__(selected_region, max_tracked_ships, update_interval, auto_map_update_seconds)` - Initialize tracker
- `start()` - Start tracking vessels
- `stop()` - Stop tracker and save final map

**Example:**
```python
from tankers_tracker import TankersTracker

tracker = TankersTracker(
    selected_region="persian_gulf",
    max_tracked_ships=100,
    update_interval=2
)
tracker.start()
```

---

### AISClient

WebSocket client for AIS Stream.

**Methods:**

- `__init__(region_bounds, max_vessels, on_static_data, on_position_update)` - Initialize client
- `connect()` - Connect to AIS Stream
- `get_vessels()` - Get all tracked vessels
- `get_active_vessels()` - Get vessels with valid positions

---

### MapGenerator

Generates interactive maps with Folium.

**Methods:**

- `__init__(region_name, output_file)` - Initialize map generator
- `create_base_map()` - Create base map
- `add_ports(m)` - Add port markers
- `add_vessels(m, vessels)` - Add vessel markers
- `generate_map(vessels, auto_open)` - Generate complete map

---

### Vessel

Data model for tracked vessels.

**Attributes:**

- `mmsi`: Maritime Mobile Service Identity (int)
- `lat`: Latitude (float)
- `lon`: Longitude (float)
- `name`: Vessel name (str)
- `speed`: Speed in knots (float)
- `course`: Course in degrees (float)
- `destination`: Destination port (str)
- `ship_type`: IMO ship type code (int)
- `last_update`: Last update timestamp (str)

**Methods:**

- `update_position(lat, lon, speed, course, timestamp)` - Update position
- `update_static_data(name, destination, ship_type)` - Update static data
- `has_position()` - Check if vessel has valid position
- `is_tanker(tanker_types)` - Check if vessel is a tanker
- `to_dict()` - Convert to dictionary

---

### Region

Geographical region model.

**Attributes:**

- `name`: Region identifier (str)
- `bounds`: Bounding box [[south, west], [north, east]] (list)
- `ports`: List of ports (list[Port])

**Properties:**

- `center` - Get center coordinates
- `bounding_box` - Get bounding box for AIS subscription

**Methods:**

- `contains_point(lat, lon)` - Check if point is in region

---

## Configuration

All configuration is in `src/config.py`:

### Environment Variables

- `AIS_API_KEY` - Your AIS Stream API key
- `MAX_TRACKED_SHIPS` - Maximum vessels to track (default: 100)
- `UPDATE_INTERVAL` - Update map every N positions (default: 2)
- `AUTO_MAP_UPDATE_SECONDS` - Auto-refresh interval (default: 10)
- `LOG_LEVEL` - Logging level (default: INFO)

### Available Regions

- `persian_gulf` - Persian Gulf and Strait of Hormuz
- `singapore_strait` - Singapore and Malacca Strait
- `suez_canal` - Suez Canal area
- `us_gulf` - US Gulf of Mexico
- `north_sea` - North Sea
- `mediterranean` - Mediterranean Sea
- `malacca` - Strait of Malacca
- `gibraltar` - Strait of Gibraltar
- `panama` - Panama Canal

### Ship Types

Tanker types (70-89):
- 70-74: Cargo (various hazard classes)
- 80-84: Tankers (various hazard classes)

---

## Events and Callbacks

The `AISClient` supports callbacks for vessel events:

```python
def on_static_data(vessel: Vessel):
    print(f"Received info for {vessel.name}")

def on_position_update(vessel: Vessel):
    print(f"{vessel.name} at {vessel.lat}, {vessel.lon}")

client = AISClient(
    region_bounds=[[22, 48], [30, 60]],
    on_static_data=on_static_data,
    on_position_update=on_position_update
)
```

---

## Error Handling

The application handles:

- WebSocket connection errors (auto-reconnect)
- JSON parsing errors (skipped)
- Missing data fields (logged as warnings)
- Invalid regions (falls back to worldwide tracking)

---

## Performance Tips

1. **Reduce max_tracked_ships** - Track fewer vessels for better performance
2. **Increase update_interval** - Update map less frequently
3. **Use specific regions** - Smaller bounding boxes = less data
4. **Disable auto-refresh** - Set auto_map_update_seconds to a higher value

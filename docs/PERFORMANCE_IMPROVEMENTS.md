# Performance Improvements & Architecture Enhancements

## 🚀 Overview

The tankers tracker has been significantly enhanced to track **more ships faster** with **comprehensive vessel information**.

---

## ✨ Major Improvements

### 1. **Enhanced Vessel Data Model**

The `Vessel` model now includes **25+ data fields**:

#### Position Data
- `lat`, `lon` - GPS coordinates
- `speed`, `course` - Navigation data
- `heading` - True heading
- `rot` - Rate of turn
- `navigational_status` - Current status (anchored, under way, etc.)
- `position_accuracy` - GPS accuracy indicator

#### Static Vessel Information
- `name` - Vessel name
- `imo` - IMO number (international registry)
- `callsign` - Radio callsign
- `ship_type` - IMO ship type code

#### Vessel Dimensions
- `length`, `width` - Overall dimensions
- `draught` - Current water depth
- `dimension_to_bow/stern/port/starboard` - GPS antenna position

#### Voyage Information
- `destination` - Destination port
- `eta` - Estimated time of arrival
- `cargo` - Cargo type
- `deadweight` - Deadweight tonnage (DWT)
- `gross_tonnage` - Gross tonnage (GT)

#### Tracking Metadata
- `last_update` - Last position update time
- `first_seen` - When vessel was first detected
- `update_count` - Number of updates received

---

### 2. **Performance Optimizations**

#### Concurrent Message Processing
- **Batched processing**: Messages processed in batches of 10 (configurable)
- **Async operations**: Non-blocking message handling
- **Queue-based architecture**: Prevents bottlenecks during high traffic

#### Increased Capacity
- **Max vessels**: Increased from 100 to **500** by default
- **Faster updates**: Optimized update intervals
- **Efficient memory usage**: Smart caching strategies

#### Database Caching
- **SQLite database**: Persistent vessel storage
- **Fast lookups**: Indexed queries for quick access
- **Historical data**: Vessels persist across sessions
- **Bulk operations**: Efficient batch saves

---

### 3. **New Architecture Components**

#### VesselDatabase (`vessel_database.py`)
```python
# Provides:
- SQLite-based persistent storage
- Indexed queries for fast lookups
- Vessel history tracking
- Statistics and analytics
```

#### VesselInfoService (`vessel_info_service.py`)
```python
# Features:
- In-memory cache + database layer
- Intelligent data merging
- Vessel enrichment (calculated fields)
- Service statistics
```

#### Enhanced AIS Client
```python
# Improvements:
- Concurrent message processing
- Message batching (10 messages/batch)
- Priority handling for tankers
- Auto-reconnect on failure
- Comprehensive data extraction
```

#### Enhanced Map Generator
```python
# Features:
- Rich vessel popups (10+ fields)
- Real-time statistics overlay
- Better tooltips
- Performance optimizations
```

---

## 📊 Configuration Options

### Environment Variables (.env)

```bash
# Tracking Settings
MAX_TRACKED_SHIPS=500              # How many vessels to track
UPDATE_INTERVAL=5                  # Update map every N positions
AUTO_MAP_UPDATE_SECONDS=15         # Auto-refresh interval

# Performance Settings
ENABLE_CONCURRENT_PROCESSING=true  # Enable batched processing
MESSAGE_BATCH_SIZE=10              # Messages per batch
USE_DATABASE_CACHE=true            # Enable SQLite caching
DATABASE_PATH=data/vessels.db      # Database file location

# AIS Stream Settings
AIS_API_KEY=your_key_here          # Your API key
```

---

## 🎯 Performance Comparison

### Before Enhancements
- Max vessels: 100
- Data fields: 9
- Processing: Sequential
- Storage: Memory only
- Map updates: Basic info

### After Enhancements
- Max vessels: **500** (5x increase)
- Data fields: **25+** (3x more information)
- Processing: **Concurrent batched**
- Storage: **Memory + SQLite database**
- Map updates: **Comprehensive vessel details**

---

## 💡 Usage Examples

### Basic Usage (Default Settings)

```python
from tankers_tracker import TankersTracker

tracker = TankersTracker(
    selected_region="persian_gulf",
    max_tracked_ships=500,
    update_interval=5,
    auto_map_update_seconds=15
)

tracker.start()
```

### High-Performance Configuration

```python
# Track many vessels quickly
tracker = TankersTracker(
    selected_region="singapore_strait",
    max_tracked_ships=1000,          # Track up to 1000 vessels
    update_interval=10,              # Less frequent map updates
    auto_map_update_seconds=30,      # Slower auto-refresh
    use_database=True,               # Enable caching
    enable_concurrent=True           # Enable batching
)
```

### Memory-Only Mode (No Database)

```python
# For quick testing without persistence
tracker = TankersTracker(
    selected_region="suez_canal",
    max_tracked_ships=200,
    use_database=False,              # Disable database
    enable_concurrent=True
)
```

---

## 📈 Database Features

### Persistent Storage

Vessels are automatically saved to SQLite database:

```python
from utils.vessel_database import VesselDatabase

db = VesselDatabase("data/vessels.db")

# Get vessel by MMSI
vessel = db.get_vessel(123456789)

# Get all tankers
tankers = db.get_vessels_by_type([80, 81, 82, 83, 84])

# Get statistics
stats = db.get_statistics()
print(f"Total vessels: {stats['total_vessels']}")
print(f"Tankers: {stats['tankers']}")
```

### Vessel Info Service

High-level API for vessel management:

```python
from utils.vessel_info_service import VesselInfoService

service = VesselInfoService(use_database=True)

# Get all active vessels
active = service.get_active_vessels()

# Get only tankers
tankers = service.get_tankers([80, 81, 82, 83, 84])

# Get statistics
stats = service.get_statistics()
print(f"Cache size: {stats['cache_size']}")
print(f"Active vessels: {stats['active_vessels']}")
```

---

## 🗺️ Enhanced Map Information

Each vessel marker now shows:

### Basic Info
- Vessel name / MMSI
- Ship type
- IMO number
- Callsign

### Navigation
- Speed (knots)
- Course (degrees)
- Heading (if available)
- Navigation status (anchored, under way, etc.)

### Voyage
- Destination port
- ETA (if available)

### Dimensions
- Length × Width
- Draught

### Position
- Latitude, Longitude (4 decimal precision)
- Update count
- Last seen time

---

## ⚡ Performance Tips

### For Maximum Speed

1. **Increase batch size**: `MESSAGE_BATCH_SIZE=20`
2. **Reduce map updates**: `UPDATE_INTERVAL=10`
3. **Enable concurrent processing**: `ENABLE_CONCURRENT_PROCESSING=true`
4. **Use database caching**: `USE_DATABASE_CACHE=true`

### For Maximum Accuracy

1. **Smaller update interval**: `UPDATE_INTERVAL=2`
2. **Faster auto-refresh**: `AUTO_MAP_UPDATE_SECONDS=5`
3. **Enable all features**: All settings enabled

### For High-Traffic Regions

```python
tracker = TankersTracker(
    selected_region="singapore_strait",  # Busy region
    max_tracked_ships=1000,
    update_interval=10,
    auto_map_update_seconds=20,
    use_database=True,
    enable_concurrent=True
)
```

---

## 🔧 Technical Details

### Concurrent Processing Flow

```
WebSocket → Message Queue → Batch Processor
                                    ↓
                            [Process 10 messages]
                                    ↓
                            Update Vessel Service
                                    ↓
                            Cache + Database
                                    ↓
                            Callback → Map Update
```

### Data Persistence Flow

```
AIS Message → Vessel Model → Vessel Service → Database
                                    ↓
                            In-Memory Cache
                                    ↓
                            Fast Retrieval
```

---

## 📦 New Dependencies

No additional dependencies required! All enhancements use:
- Python standard library (`sqlite3`, `asyncio`, `threading`)
- Existing dependencies (`folium`, `websockets`)

---

## 🎓 Learning Resources

### Understanding AIS Data
- Navigation status codes: 0-15 (anchored, under way, etc.)
- Ship type codes: 70-89 for tankers/cargo
- IMO numbers: Unique vessel identifiers
- MMSI: Maritime Mobile Service Identity

### Database Schema
```sql
-- Vessels table with 25+ columns
CREATE TABLE vessels (
    mmsi INTEGER PRIMARY KEY,
    lat REAL, lon REAL,
    speed REAL, course REAL,
    name TEXT, imo INTEGER,
    -- ... and 20+ more fields
)
```

---

## 🚦 Migration Guide

### Upgrading from Previous Version

1. **No breaking changes** - existing code works as-is
2. **New features are opt-in** - defaults preserve old behavior
3. **Database auto-creates** on first run
4. **Backward compatible** - old maps still work

### Recommended Changes

```python
# Old configuration
tracker = TankersTracker(
    selected_region="persian_gulf",
    max_tracked_ships=100,
    update_interval=2,
    auto_map_update_seconds=10
)

# New recommended configuration
tracker = TankersTracker(
    selected_region="persian_gulf",
    max_tracked_ships=500,           # ← Increased
    update_interval=5,               # ← Adjusted for performance
    auto_map_update_seconds=15,      # ← Optimized
    use_database=True,               # ← NEW: Enable caching
    enable_concurrent=True           # ← NEW: Enable batching
)
```

---

## 📞 Support & Troubleshooting

### Database Issues

If database errors occur:
```bash
# Delete and recreate
rm data/vessels.db
# Tracker will recreate on next run
```

### Performance Issues

If tracking is slow:
1. Increase `UPDATE_INTERVAL` to 10+
2. Increase `MESSAGE_BATCH_SIZE` to 20
3. Reduce `max_tracked_ships` to 200

### Memory Issues

If running out of memory:
1. Enable database: `use_database=True`
2. Reduce cache: `max_tracked_ships=300`
3. Disable concurrent: `enable_concurrent=False`

---

## 🎉 Summary

The enhanced tankers tracker provides:

✅ **5x more vessel capacity** (100 → 500+)
✅ **3x more vessel information** (9 → 25+ fields)
✅ **Concurrent processing** for speed
✅ **Database caching** for persistence
✅ **Rich map display** with comprehensive data
✅ **Production-ready** architecture
✅ **Backward compatible** with existing code

**Result**: Track more ships faster with accurate, comprehensive information!

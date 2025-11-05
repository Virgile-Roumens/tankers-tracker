# 🚀 Quick Start - Enhanced Tankers Tracker

## What's New?

Your tankers tracker now has **5x the capacity** and **3x more vessel information** with enhanced performance!

---

## ⚡ Quick Start (3 Steps)

### 1. Run the Enhanced Tracker

```bash
cd "c:\Users\Virgile ROUMENS\Desktop\Trading Commo GNV\tankers-tracker\src"
python tankers_tracker.py
```

That's it! The tracker now:
- ✅ Tracks up to **500 vessels** (was 100)
- ✅ Shows **25+ fields** per vessel (was 9)
- ✅ Uses **database caching** for persistence
- ✅ Processes messages **concurrently** for speed

### 2. Click on Any Vessel

Open the map and click any vessel marker to see:
- **Identity**: Name, MMSI, IMO, Callsign
- **Navigation**: Speed, Course, Heading, Status
- **Voyage**: Destination, ETA
- **Dimensions**: Length × Width, Draught
- **Position**: High-precision GPS, accuracy
- **History**: Update count, first/last seen

### 3. Check the Database

After running for a few minutes, check your vessel database:

```python
from utils.vessel_database import VesselDatabase

db = VesselDatabase()
stats = db.get_statistics()
print(f"Total vessels in DB: {stats['total_vessels']}")
print(f"Tankers: {stats['tankers']}")
```

---

## 🎮 Configuration Examples

### Default (Recommended)

```python
from tankers_tracker import TankersTracker

tracker = TankersTracker()  # Uses enhanced defaults
tracker.start()
```

### High-Capacity Mode

```python
# Track 1000+ vessels in busy regions
tracker = TankersTracker(
    selected_region="singapore_strait",
    max_tracked_ships=1000,
    update_interval=10,
    auto_map_update_seconds=30
)
tracker.start()
```

### Maximum Detail Mode

```python
# Get every update with full details
tracker = TankersTracker(
    selected_region="persian_gulf",
    max_tracked_ships=300,
    update_interval=1,              # Update map on every position
    auto_map_update_seconds=5       # Refresh every 5 seconds
)
tracker.start()
```

---

## 📊 New Features Highlights

### 1. Comprehensive Vessel Data

**25+ fields per vessel** including:
- IMO number (international registry ID)
- Callsign (radio identification)
- Vessel dimensions (length, width, draught)
- Navigation status (anchored, under way, moored, etc.)
- ETA and destination
- Rate of turn, true heading
- GPS accuracy indicator

### 2. Database Persistence

All vessel data is automatically saved to SQLite:
```
data/vessels.db  ← Created automatically
```

Benefits:
- Vessels persist across sessions
- Fast lookups with indexed queries
- Historical tracking
- Statistics and analytics

### 3. Concurrent Processing

Messages are processed in batches of 10 for **much faster** performance:
- Non-blocking message handling
- Optimized for high-traffic regions
- Better CPU utilization

### 4. Enhanced Map Display

- **Rich popups**: 10+ fields of information per vessel
- **Statistics overlay**: Real-time vessel count & region info
- **Better tooltips**: Name, speed, destination at a glance
- **Color coding**: Tankers in dark red, others in orange

---

## 🔧 Configuration File (.env)

Create/edit `.env` in the root directory:

```bash
# Tracking capacity
MAX_TRACKED_SHIPS=500

# Performance
ENABLE_CONCURRENT_PROCESSING=true
MESSAGE_BATCH_SIZE=10
USE_DATABASE_CACHE=true
DATABASE_PATH=data/vessels.db

# Update intervals
UPDATE_INTERVAL=5
AUTO_MAP_UPDATE_SECONDS=15

# API
AIS_API_KEY=77751d32bae3caa0b20f2d7099f03ef5b836fb4c
```

---

## 📈 Performance Comparison

### Before Enhancements
```
Max vessels: 100
Data per vessel: 9 fields
Processing: Sequential (slow)
Storage: Memory only (lost on restart)
Map updates: Basic info
```

### After Enhancements
```
Max vessels: 500+ (5x more!)
Data per vessel: 25+ fields (3x more!)
Processing: Concurrent batched (fast!)
Storage: Memory + SQLite (persistent!)
Map updates: Comprehensive info
```

---

## 💡 Tips & Tricks

### For Best Performance

1. **Increase batch size** for faster processing:
   ```python
   # In config.py or .env
   MESSAGE_BATCH_SIZE=20  # Process 20 messages at once
   ```

2. **Reduce map updates** in busy regions:
   ```python
   tracker = TankersTracker(
       update_interval=10,  # Update every 10 positions
       auto_map_update_seconds=30  # Auto-refresh every 30s
   )
   ```

3. **Use database caching** for persistence:
   ```python
   tracker = TankersTracker(use_database=True)
   ```

### For Maximum Detail

1. **Update more frequently**:
   ```python
   tracker = TankersTracker(
       update_interval=1,  # Every position
       auto_map_update_seconds=5  # Every 5 seconds
   )
   ```

2. **Focus on smaller region**:
   ```python
   tracker = TankersTracker(
       selected_region="suez_canal",  # Small, focused area
       max_tracked_ships=200
   )
   ```

### Accessing Vessel Data Programmatically

```python
from utils.vessel_info_service import VesselInfoService

service = VesselInfoService()

# Get all active vessels
active_vessels = service.get_active_vessels()

# Get only tankers
tankers = service.get_tankers([80, 81, 82, 83, 84])

# Get specific vessel
vessel = service.get_vessel(mmsi=123456789)
if vessel:
    print(f"{vessel.name}")
    print(f"  Size: {vessel.length}m × {vessel.width}m")
    print(f"  Draught: {vessel.draught}m")
    print(f"  Destination: {vessel.destination}")
    print(f"  ETA: {vessel.eta}")

# Get statistics
stats = service.get_statistics()
print(f"Total vessels: {stats['total_vessels']}")
print(f"Active vessels: {stats['active_vessels']}")
```

---

## 🗺️ Available Regions

All regions now support enhanced tracking:

```python
regions = [
    "persian_gulf",      # Persian Gulf & Hormuz
    "singapore_strait",  # Singapore & Malacca (busy!)
    "suez_canal",        # Suez Canal
    "us_gulf",           # US Gulf of Mexico
    "north_sea",         # North Sea
    "mediterranean",     # Mediterranean Sea
    "malacca",           # Strait of Malacca
    "gibraltar",         # Strait of Gibraltar
    "panama"             # Panama Canal
]
```

---

## 🐛 Troubleshooting

### Database locked error
```bash
# Delete and recreate
rm data/vessels.db
# Will auto-recreate on next run
```

### Too many vessels, slow performance
```python
# Reduce capacity and increase intervals
tracker = TankersTracker(
    max_tracked_ships=200,
    update_interval=10,
    auto_map_update_seconds=30
)
```

### Want to disable database
```python
tracker = TankersTracker(use_database=False)
```

### Want to disable concurrent processing
```python
tracker = TankersTracker(enable_concurrent=False)
```

---

## 📚 Documentation

- **ENHANCEMENTS_SUMMARY.md** - Complete overview of all improvements
- **PERFORMANCE_IMPROVEMENTS.md** - Detailed performance guide
- **API.md** - Updated API documentation
- **README.md** - General project information

---

## ✅ What to Expect

When you run the enhanced tracker:

1. **Startup**: Loads cached vessels from database
2. **Connection**: Connects to AIS stream
3. **Processing**: Messages processed in concurrent batches
4. **Display**: Rich vessel information on map
5. **Updates**: Automatic map refresh every 15 seconds
6. **Persistence**: All data saved to database
7. **Shutdown**: Statistics displayed, database saved

---

## 🎉 You're Ready!

Just run:
```bash
cd src
python tankers_tracker.py
```

Then:
1. ✅ Watch vessels appear on the map
2. ✅ Click any vessel to see 25+ fields of data
3. ✅ See concurrent processing in action
4. ✅ Check `data/vessels.db` for persistent storage
5. ✅ Enjoy tracking **hundreds** of tankers with **comprehensive** information!

**Happy tracking! 🛢️⚓🗺️**

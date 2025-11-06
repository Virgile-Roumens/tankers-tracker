"""
Vessel database for caching and persistent storage.

Provides SQLite-based caching for vessel data to enable:
- Faster lookups of historical vessel information
- Persistent storage across sessions
- Quick access to vessel static data
- Performance optimization for large vessel counts
"""

import sqlite3
import json
import logging
from typing import Optional, Dict, List
from datetime import datetime
from pathlib import Path

from models.vessel import Vessel
from enums.ship_type import ShipType
from enums.navigational_status import NavigationalStatus

logger = logging.getLogger(__name__)


class VesselDatabase:
    """
    SQLite database for vessel information caching.
    """
    
    def __init__(self, db_path: str = "data/vessels.db"):
        """
        Initialize vessel database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        
        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Create database tables if they don't exist."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            
            cursor = self.conn.cursor()
            
            # Create vessels table with comprehensive schema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vessels (
                    mmsi INTEGER PRIMARY KEY,
                    
                    -- Position data
                    lat REAL,
                    lon REAL,
                    speed REAL,
                    course REAL,
                    heading INTEGER,
                    rot REAL,
                    navigational_status INTEGER,
                    position_accuracy INTEGER,
                    
                    -- Static data
                    name TEXT,
                    imo INTEGER,
                    callsign TEXT,
                    ship_type INTEGER,
                    
                    -- Dimensions
                    length REAL,
                    width REAL,
                    draught REAL,
                    dimension_to_bow INTEGER,
                    dimension_to_stern INTEGER,
                    dimension_to_port INTEGER,
                    dimension_to_starboard INTEGER,
                    
                    -- Voyage data
                    destination TEXT,
                    eta TEXT,
                    cargo TEXT,
                    deadweight INTEGER,
                    gross_tonnage INTEGER,
                    
                    -- Metadata
                    last_update TEXT,
                    first_seen TEXT,
                    update_count INTEGER,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create index on MMSI for fast lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_mmsi ON vessels(mmsi)
            ''')
            
            # Create index on ship type for filtering
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_ship_type ON vessels(ship_type)
            ''')
            
            # Create index on last update for sorting
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_last_update ON vessels(last_update)
            ''')
            
            # Add region tracking columns if they don't exist (migration-safe)
            try:
                cursor.execute('ALTER TABLE vessels ADD COLUMN current_region TEXT')
                logger.info("Added current_region column to database")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                cursor.execute('ALTER TABLE vessels ADD COLUMN last_region_update TEXT')
                logger.info("Added last_region_update column to database")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Create region index
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_region ON vessels(current_region)
            ''')
            
            # Create position index for spatial queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_position ON vessels(lat, lon)
            ''')
            
            # Create vessel history table for trajectory tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vessel_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mmsi INTEGER NOT NULL,
                    lat REAL NOT NULL,
                    lon REAL NOT NULL,
                    speed REAL,
                    course REAL,
                    heading INTEGER,
                    timestamp TEXT NOT NULL,
                    region TEXT,
                    FOREIGN KEY (mmsi) REFERENCES vessels(mmsi)
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_history_mmsi ON vessel_history(mmsi)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_history_timestamp ON vessel_history(timestamp)
            ''')
            
            self.conn.commit()
            logger.info(f"✅ Vessel database initialized at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def save_vessel(self, vessel: Vessel):
        """
        Save or update vessel in database.
        
        Args:
            vessel: Vessel object to save
        """
        try:
            cursor = self.conn.cursor()
            
            # Sanitize data to prevent dict/list objects
            def sanitize_value(value, preserve_numeric=False):
                """Convert complex data types to strings or None."""
                if value is None:
                    return None
                elif isinstance(value, (dict, list, tuple)):
                    return str(value)  # Convert to string representation
                elif isinstance(value, (int, float)):
                    return value  # Keep numeric values as-is
                elif isinstance(value, str):
                    return value
                else:
                    return str(value)  # Convert other types to string
            
            # Prepare sanitized parameters (preserve numeric values for ship_type, etc.)
            # Convert ShipType enum to int value for database storage
            ship_type_value = vessel.ship_type.value if isinstance(vessel.ship_type, ShipType) else vessel.ship_type
            
            # Convert NavigationalStatus enum to int value for database storage
            nav_status_value = vessel.navigational_status.value if isinstance(vessel.navigational_status, NavigationalStatus) else vessel.navigational_status
            
            params = (
                vessel.mmsi, vessel.lat, vessel.lon, vessel.speed, vessel.course,
                vessel.heading, vessel.rot, nav_status_value, vessel.position_accuracy,
                sanitize_value(vessel.name), vessel.imo, sanitize_value(vessel.callsign), ship_type_value,
                vessel.length, vessel.width, vessel.draught,
                vessel.dimension_to_bow, vessel.dimension_to_stern,
                vessel.dimension_to_port, vessel.dimension_to_starboard,
                sanitize_value(vessel.destination), sanitize_value(vessel.eta), sanitize_value(vessel.cargo),
                vessel.deadweight, vessel.gross_tonnage,
                sanitize_value(vessel.last_update), sanitize_value(vessel.first_seen), vessel.update_count
            )
            
            cursor.execute('''
                INSERT OR REPLACE INTO vessels (
                    mmsi, lat, lon, speed, course, heading, rot,
                    navigational_status, position_accuracy,
                    name, imo, callsign, ship_type,
                    length, width, draught,
                    dimension_to_bow, dimension_to_stern,
                    dimension_to_port, dimension_to_starboard,
                    destination, eta, cargo, deadweight, gross_tonnage,
                    last_update, first_seen, update_count,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', params)
            
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Failed to save vessel {vessel.mmsi}: {e}")
            # Debug information for troubleshooting
            try:
                logger.debug(f"Vessel data that failed: ETA={repr(vessel.eta)}, Destination={repr(vessel.destination)}, Name={repr(vessel.name)}, Ship_Type={repr(vessel.ship_type)}")
            except:
                pass
    
    def get_vessel(self, mmsi: int) -> Optional[Vessel]:
        """
        Retrieve vessel from database.
        
        Args:
            mmsi: Vessel MMSI number
            
        Returns:
            Vessel object if found, None otherwise
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM vessels WHERE mmsi = ?', (mmsi,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_vessel(row)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get vessel {mmsi}: {e}")
            return None
    
    def get_all_vessels(self) -> List[Vessel]:
        """
        Get all vessels from database.
        
        Returns:
            List of Vessel objects
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM vessels ORDER BY last_update DESC')
            rows = cursor.fetchall()
            
            return [self._row_to_vessel(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get all vessels: {e}")
            return []
    
    def get_vessels_by_type(self, ship_types: List[int]) -> List[Vessel]:
        """
        Get vessels filtered by ship type.
        
        Args:
            ship_types: List of ship type codes
            
        Returns:
            List of matching Vessel objects
        """
        try:
            cursor = self.conn.cursor()
            placeholders = ','.join('?' * len(ship_types))
            cursor.execute(
                f'SELECT * FROM vessels WHERE ship_type IN ({placeholders}) ORDER BY last_update DESC',
                ship_types
            )
            rows = cursor.fetchall()
            
            return [self._row_to_vessel(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get vessels by type: {e}")
            return []
    
    def _row_to_vessel(self, row: sqlite3.Row) -> Vessel:
        """
        Convert database row to Vessel object.
        
        Args:
            row: SQLite row object
            
        Returns:
            Vessel object
        """
        # Convert ship_type integer back to ShipType enum
        ship_type_value = row['ship_type']
        ship_type = ShipType.from_code(ship_type_value) if ship_type_value is not None else None
        
        # Convert navigational_status integer back to NavigationalStatus enum
        nav_status_value = row['navigational_status']
        navigational_status = NavigationalStatus.from_code(nav_status_value) if nav_status_value is not None else None
        
        return Vessel(
            mmsi=row['mmsi'],
            lat=row['lat'],
            lon=row['lon'],
            speed=row['speed'],
            course=row['course'],
            heading=row['heading'],
            rot=row['rot'],
            navigational_status=navigational_status,
            position_accuracy=row['position_accuracy'],
            name=row['name'],
            imo=row['imo'],
            callsign=row['callsign'],
            ship_type=ship_type,
            length=row['length'],
            width=row['width'],
            draught=row['draught'],
            dimension_to_bow=row['dimension_to_bow'],
            dimension_to_stern=row['dimension_to_stern'],
            dimension_to_port=row['dimension_to_port'],
            dimension_to_starboard=row['dimension_to_starboard'],
            destination=row['destination'],
            eta=row['eta'],
            cargo=row['cargo'],
            deadweight=row['deadweight'],
            gross_tonnage=row['gross_tonnage'],
            last_update=row['last_update'],
            first_seen=row['first_seen'],
            update_count=row['update_count']
        )
    
    def bulk_save(self, vessels: Dict[int, Vessel]):
        """
        Save multiple vessels efficiently.
        
        Args:
            vessels: Dictionary of vessels keyed by MMSI
        """
        try:
            for vessel in vessels.values():
                self.save_vessel(vessel)
            
            logger.info(f"💾 Saved {len(vessels)} vessels to database")
            
        except Exception as e:
            logger.error(f"Failed to bulk save vessels: {e}")
    
    def get_statistics(self) -> Dict:
        """
        Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('SELECT COUNT(*) as total FROM vessels')
            total = cursor.fetchone()['total']
            
            cursor.execute('SELECT COUNT(*) as tankers FROM vessels WHERE ship_type >= 70 AND ship_type < 90')
            tankers = cursor.fetchone()['tankers']
            
            cursor.execute('SELECT COUNT(*) as with_position FROM vessels WHERE lat IS NOT NULL AND lon IS NOT NULL')
            with_position = cursor.fetchone()['with_position']
            
            return {
                'total_vessels': total,
                'tankers': tankers,
                'with_position': with_position
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def fix_missing_ship_types(self):
        """
        Fix vessels that might have missing ship_type data.
        This can happen when AIS data arrives out of order.
        """
        try:
            cursor = self.conn.cursor()
            
            # Count vessels with missing ship_type
            cursor.execute('SELECT COUNT(*) FROM vessels WHERE ship_type IS NULL')
            missing_count = cursor.fetchone()[0]
            
            if missing_count > 0:
                logger.info(f"🔧 Found {missing_count} vessels with missing ship_type - this will be corrected as new AIS data arrives")
                
                # For debugging: show some examples
                cursor.execute('SELECT mmsi, name FROM vessels WHERE ship_type IS NULL AND name IS NOT NULL LIMIT 5')
                examples = cursor.fetchall()
                if examples:
                    logger.debug("Examples of vessels needing ship_type:")
                    for mmsi, name in examples:
                        logger.debug(f"  - {name} (MMSI: {mmsi})")
        
        except Exception as e:
            logger.error(f"Failed to fix missing ship types: {e}")
    
    def save_vessel_history(self, mmsi: int, lat: float, lon: float, 
                           speed: Optional[float] = None, 
                           course: Optional[float] = None,
                           heading: Optional[int] = None,
                           region: Optional[str] = None) -> None:
        """
        Save vessel position to history for trajectory tracking.
        
        Args:
            mmsi: Vessel MMSI
            lat: Latitude
            lon: Longitude
            speed: Speed in knots
            course: Course in degrees
            heading: Heading in degrees
            region: Current region
        """
        try:
            cursor = self.conn.cursor()
            timestamp = datetime.utcnow().isoformat()
            
            cursor.execute('''
                INSERT INTO vessel_history 
                (mmsi, lat, lon, speed, course, heading, timestamp, region)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (mmsi, lat, lon, speed, course, heading, timestamp, region))
            
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Error saving vessel history: {e}")
    
    def get_vessel_history(self, mmsi: int, limit: int = 100) -> List[Dict]:
        """
        Get historical positions for a vessel.
        
        Args:
            mmsi: Vessel MMSI
            limit: Maximum number of records to return
            
        Returns:
            List of historical position dictionaries
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT lat, lon, speed, course, heading, timestamp, region
                FROM vessel_history
                WHERE mmsi = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (mmsi, limit))
            
            rows = cursor.fetchall()
            return [
                {
                    'lat': row['lat'],
                    'lon': row['lon'],
                    'speed': row['speed'],
                    'course': row['course'],
                    'heading': row['heading'],
                    'timestamp': row['timestamp'],
                    'region': row['region']
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Error getting vessel history: {e}")
            return []
    
    def update_vessel_region(self, mmsi: int, region: str) -> None:
        """
        Update the current region for a vessel.
        
        Args:
            mmsi: Vessel MMSI
            region: Region name
        """
        try:
            cursor = self.conn.cursor()
            timestamp = datetime.utcnow().isoformat()
            
            cursor.execute('''
                UPDATE vessels
                SET current_region = ?, last_region_update = ?
                WHERE mmsi = ?
            ''', (region, timestamp, mmsi))
            
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Error updating vessel region: {e}")
    
    def get_vessels_by_region(self, region: str) -> List[Vessel]:
        """
        Get all vessels in a specific region.
        
        Args:
            region: Region name
            
        Returns:
            List of Vessel objects
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM vessels
                WHERE current_region = ?
                ORDER BY last_update DESC
            ''', (region,))
            
            rows = cursor.fetchall()
            return [self._row_to_vessel(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting vessels by region: {e}")
            return []
    
    def cleanup_old_history(self, days: int = 7) -> int:
        """
        Remove vessel history older than specified days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of records deleted
        """
        try:
            from datetime import timedelta
            cursor = self.conn.cursor()
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            cursor.execute('''
                DELETE FROM vessel_history
                WHERE timestamp < ?
            ''', (cutoff_date,))
            
            deleted = cursor.rowcount
            self.conn.commit()
            
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} old history records")
            return deleted
            
        except Exception as e:
            logger.error(f"Error cleaning up history: {e}")
            return 0

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close()

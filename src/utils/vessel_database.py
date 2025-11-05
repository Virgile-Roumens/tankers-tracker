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
            ''', (
                vessel.mmsi, vessel.lat, vessel.lon, vessel.speed, vessel.course,
                vessel.heading, vessel.rot, vessel.navigational_status, vessel.position_accuracy,
                vessel.name, vessel.imo, vessel.callsign, vessel.ship_type,
                vessel.length, vessel.width, vessel.draught,
                vessel.dimension_to_bow, vessel.dimension_to_stern,
                vessel.dimension_to_port, vessel.dimension_to_starboard,
                vessel.destination, vessel.eta, vessel.cargo,
                vessel.deadweight, vessel.gross_tonnage,
                vessel.last_update, vessel.first_seen, vessel.update_count
            ))
            
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Failed to save vessel {vessel.mmsi}: {e}")
    
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
        return Vessel(
            mmsi=row['mmsi'],
            lat=row['lat'],
            lon=row['lon'],
            speed=row['speed'],
            course=row['course'],
            heading=row['heading'],
            rot=row['rot'],
            navigational_status=row['navigational_status'],
            position_accuracy=row['position_accuracy'],
            name=row['name'],
            imo=row['imo'],
            callsign=row['callsign'],
            ship_type=row['ship_type'],
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
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close()

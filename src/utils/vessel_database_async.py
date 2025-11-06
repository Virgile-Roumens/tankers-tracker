"""
Async Vessel Database using aiosqlite for high-performance I/O.

Provides non-blocking database operations for vessel tracking,
significantly improving throughput in concurrent scenarios.
"""

import aiosqlite
import logging
from typing import Optional, Dict, List
from datetime import datetime
from pathlib import Path

from models.vessel import Vessel
from enums.ship_type import ShipType
from enums.navigational_status import NavigationalStatus

logger = logging.getLogger(__name__)


class VesselDatabaseAsync:
    """
    Async SQLite database for vessel information caching.
    Uses aiosqlite for non-blocking I/O operations.
    """
    
    def __init__(self, db_path: str = "data/vessels.db"):
        """Initialize async vessel database."""
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.initialized = False
    
    async def initialize(self):
        """Initialize database tables asynchronously."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.cursor()
            
            # Create vessels table
            await cursor.execute('''
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
            
            # Create indexes for fast queries
            await cursor.execute('CREATE INDEX IF NOT EXISTS idx_mmsi ON vessels(mmsi)')
            await cursor.execute('CREATE INDEX IF NOT EXISTS idx_ship_type ON vessels(ship_type)')
            await cursor.execute('CREATE INDEX IF NOT EXISTS idx_last_update ON vessels(last_update)')
            await cursor.execute('CREATE INDEX IF NOT EXISTS idx_position ON vessels(lat, lon)')
            
            await db.commit()
            self.initialized = True
            logger.info(f"✅ Async vessel database initialized at {self.db_path}")
    
    async def bulk_save(self, vessels: Dict[int, Vessel]) -> int:
        """
        Save multiple vessels efficiently in a single transaction.
        
        Args:
            vessels: Dictionary of vessels to save
            
        Returns:
            Number of vessels saved
        """
        if not vessels:
            return 0
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Prepare parameters for all vessels
                params_list = []
                for vessel in vessels.values():
                    params = self._prepare_vessel_params(vessel)
                    params_list.append(params)
                
                # Execute batch insert in single transaction
                cursor = await db.cursor()
                await cursor.executemany(
                    '''INSERT OR REPLACE INTO vessels (
                        mmsi, lat, lon, speed, course, heading, rot,
                        navigational_status, position_accuracy,
                        name, imo, callsign, ship_type,
                        length, width, draught,
                        dimension_to_bow, dimension_to_stern,
                        dimension_to_port, dimension_to_starboard,
                        destination, eta, cargo, deadweight, gross_tonnage,
                        last_update, first_seen, update_count,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)''',
                    params_list
                )
                
                await db.commit()
                logger.debug(f"💾 Batch saved {len(vessels)} vessels to database")
                return len(vessels)
                
        except Exception as e:
            logger.error(f"Failed to bulk save vessels: {e}")
            return 0
    
    async def save_vessel(self, vessel: Vessel) -> bool:
        """Save or update a single vessel."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.cursor()
                params = self._prepare_vessel_params(vessel)
                
                await cursor.execute(
                    '''INSERT OR REPLACE INTO vessels (
                        mmsi, lat, lon, speed, course, heading, rot,
                        navigational_status, position_accuracy,
                        name, imo, callsign, ship_type,
                        length, width, draught,
                        dimension_to_bow, dimension_to_stern,
                        dimension_to_port, dimension_to_starboard,
                        destination, eta, cargo, deadweight, gross_tonnage,
                        last_update, first_seen, update_count,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)''',
                    params
                )
                
                await db.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to save vessel {vessel.mmsi}: {e}")
            return False
    
    async def get_vessel(self, mmsi: int) -> Optional[Vessel]:
        """Retrieve a vessel by MMSI."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.cursor()
                await cursor.execute('SELECT * FROM vessels WHERE mmsi = ?', (mmsi,))
                row = await cursor.fetchone()
                
                if row:
                    return self._row_to_vessel(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get vessel {mmsi}: {e}")
            return None
    
    async def get_all_vessels(self) -> List[Vessel]:
        """Get all vessels from database."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.cursor()
                await cursor.execute('SELECT * FROM vessels ORDER BY last_update DESC')
                rows = await cursor.fetchall()
                
                return [self._row_to_vessel(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get all vessels: {e}")
            return []
    
    async def get_statistics(self) -> Dict:
        """Get database statistics."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.cursor()
                
                # Total vessels
                await cursor.execute('SELECT COUNT(*) as total FROM vessels')
                total = (await cursor.fetchone())['total']
                
                # Tankers
                await cursor.execute('SELECT COUNT(*) as tankers FROM vessels WHERE ship_type >= 80 AND ship_type < 90')
                tankers = (await cursor.fetchone())['tankers']
                
                # With position
                await cursor.execute('SELECT COUNT(*) as with_position FROM vessels WHERE lat IS NOT NULL AND lon IS NOT NULL')
                with_position = (await cursor.fetchone())['with_position']
                
                return {
                    'total_vessels': total,
                    'tankers': tankers,
                    'with_position': with_position
                }
                
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def _prepare_vessel_params(self, vessel: Vessel) -> tuple:
        """Prepare vessel parameters for database storage."""
        ship_type_value = vessel.ship_type.value if isinstance(vessel.ship_type, ShipType) else vessel.ship_type
        nav_status_value = vessel.navigational_status.value if isinstance(vessel.navigational_status, NavigationalStatus) else vessel.navigational_status
        
        return (
            vessel.mmsi, vessel.lat, vessel.lon, vessel.speed, vessel.course,
            vessel.heading, vessel.rot, nav_status_value, vessel.position_accuracy,
            vessel.name, vessel.imo, vessel.callsign, ship_type_value,
            vessel.length, vessel.width, vessel.draught,
            vessel.dimension_to_bow, vessel.dimension_to_stern,
            vessel.dimension_to_port, vessel.dimension_to_starboard,
            vessel.destination, vessel.eta, vessel.cargo,
            vessel.deadweight, vessel.gross_tonnage,
            vessel.last_update, vessel.first_seen, vessel.update_count
        )
    
    def _row_to_vessel(self, row) -> Vessel:
        """Convert database row to Vessel object."""
        ship_type = ShipType.from_code(row['ship_type']) if row['ship_type'] is not None else None
        nav_status = NavigationalStatus.from_code(row['navigational_status']) if row['navigational_status'] is not None else None
        
        return Vessel(
            mmsi=row['mmsi'],
            lat=row['lat'],
            lon=row['lon'],
            speed=row['speed'],
            course=row['course'],
            heading=row['heading'],
            rot=row['rot'],
            navigational_status=nav_status,
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
    
    async def close(self):
        """Close database connection."""
        logger.info("Closing async database connection")


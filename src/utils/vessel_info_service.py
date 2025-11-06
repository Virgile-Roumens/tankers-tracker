"""
Vessel Information Service for aggregating and enriching vessel data.

Provides enhanced vessel information by combining:
- AIS stream data
- Database cache
- Calculated/derived information
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime

from models.vessel import Vessel
from utils.vessel_database import VesselDatabase

logger = logging.getLogger(__name__)


class VesselInfoService:
    """
    Service for managing and enriching vessel information.
    """
    
    def __init__(self, use_database: bool = True, db_path: str = "data/vessels.db"):
        """
        Initialize vessel info service.
        
        Args:
            use_database: Whether to use database caching
            db_path: Path to database file
        """
        self.use_database = use_database
        self.db = VesselDatabase(db_path) if use_database else None
        
        # In-memory cache for fast access
        self.vessels_cache: Dict[int, Vessel] = {}
        
        # Load existing vessels from database
        if self.db:
            self._load_from_database()
    
    def _load_from_database(self):
        """Load vessels from database into cache."""
        try:
            # Check for missing ship_type data
            self.db.fix_missing_ship_types()
            
            vessels = self.db.get_all_vessels()
            for vessel in vessels:
                self.vessels_cache[vessel.mmsi] = vessel
            
            # Count how many vessels have ship_type data
            with_ship_type = len([v for v in vessels if v.ship_type is not None])
            logger.info(f"📚 Loaded {len(vessels)} vessels from database ({with_ship_type} with ship_type)")
            
        except Exception as e:
            logger.error(f"Failed to load vessels from database: {e}")
    
    def update_vessel(self, vessel: Vessel):
        """
        Update vessel information in cache and database.
        
        Args:
            vessel: Vessel object to update
        """
        # Update in-memory cache
        if vessel.mmsi in self.vessels_cache:
            # Merge with existing data to preserve information
            existing = self.vessels_cache[vessel.mmsi]
            vessel = self._merge_vessels(existing, vessel)
        
        self.vessels_cache[vessel.mmsi] = vessel
        
        # Update database
        if self.db:
            self.db.save_vessel(vessel)
    
    def _merge_vessels(self, existing: Vessel, new: Vessel) -> Vessel:
        """
        Merge vessel data, preserving non-null values.
        
        Args:
            existing: Existing vessel data
            new: New vessel data
            
        Returns:
            Merged vessel object
        """
        # Create a merged vessel starting with existing data
        merged = Vessel(mmsi=existing.mmsi)
        
        # Merge all attributes, preferring non-null new values
        for attr in ['lat', 'lon', 'speed', 'course', 'heading', 'rot',
                     'navigational_status', 'position_accuracy',
                     'name', 'imo', 'callsign', 'ship_type',
                     'length', 'width', 'draught',
                     'dimension_to_bow', 'dimension_to_stern',
                     'dimension_to_port', 'dimension_to_starboard',
                     'destination', 'eta', 'cargo', 'deadweight', 'gross_tonnage']:
            
            new_val = getattr(new, attr, None)
            existing_val = getattr(existing, attr, None)
            
            # Use new value if available, otherwise keep existing
            setattr(merged, attr, new_val if new_val is not None else existing_val)
        
        # Always use latest update time
        merged.last_update = new.last_update or existing.last_update
        
        # Keep first seen from existing
        merged.first_seen = existing.first_seen or new.first_seen
        
        # Increment update count
        merged.update_count = existing.update_count + new.update_count
        
        return merged
    
    def get_vessel(self, mmsi: int) -> Optional[Vessel]:
        """
        Get vessel by MMSI.
        
        Args:
            mmsi: Vessel MMSI number
            
        Returns:
            Vessel object if found
        """
        # Check cache first
        if mmsi in self.vessels_cache:
            return self.vessels_cache[mmsi]
        
        # Check database
        if self.db:
            vessel = self.db.get_vessel(mmsi)
            if vessel:
                self.vessels_cache[mmsi] = vessel
                return vessel
        
        return None
    
    def get_all_vessels(self) -> Dict[int, Vessel]:
        """
        Get all cached vessels.
        
        Returns:
            Dictionary of vessels keyed by MMSI
        """
        return self.vessels_cache
    
    def get_active_vessels(self) -> Dict[int, Vessel]:
        """
        Get vessels with valid position data.
        
        Returns:
            Dictionary of active vessels
        """
        return {
            mmsi: vessel 
            for mmsi, vessel in self.vessels_cache.items() 
            if vessel.has_position()
        }
    
    def get_tankers(self, tanker_types: List[int]) -> Dict[int, Vessel]:
        """
        Get all tanker vessels.
        
        Args:
            tanker_types: List of tanker ship type codes
            
        Returns:
            Dictionary of tanker vessels
        """
        return {
            mmsi: vessel 
            for mmsi, vessel in self.vessels_cache.items() 
            if vessel.is_tanker(tanker_types)
        }
    
    def get_statistics(self) -> Dict:
        """
        Get service statistics.
        
        Returns:
            Dictionary with statistics
        """
        total = len(self.vessels_cache)
        active = len(self.get_active_vessels())
        
        # Count by ship type
        ship_type_counts = {}
        for vessel in self.vessels_cache.values():
            if vessel.ship_type:
                ship_type_counts[vessel.ship_type] = ship_type_counts.get(vessel.ship_type, 0) + 1
        
        stats = {
            'total_vessels': total,
            'active_vessels': active,
            'ship_type_counts': ship_type_counts,
            'cache_size': len(self.vessels_cache)
        }
        
        # Add database stats if available
        if self.db:
            db_stats = self.db.get_statistics()
            stats.update({'database': db_stats})
        
        return stats
    
    def save_all_to_database(self):
        """Save all cached vessels to database."""
        if self.db:
            self.db.bulk_save(self.vessels_cache)
    
    def enrich_vessel_data(self, vessel: Vessel) -> Vessel:
        """
        Enrich vessel with calculated/derived information.
        
        Args:
            vessel: Vessel to enrich
            
        Returns:
            Enriched vessel
        """
        # Calculate estimated cargo capacity for tankers (rough approximation)
        if vessel.is_tanker([70, 71, 72, 73, 74, 80, 81, 82, 83, 84]):
            if vessel.length and vessel.width and vessel.draught:
                # Very rough DWT estimate: length × width × draught × coefficient
                # Typical tanker coefficient is around 0.7-0.8
                if not vessel.deadweight:
                    estimated_dwt = int(vessel.length * vessel.width * vessel.draught * 0.75)
                    vessel.deadweight = estimated_dwt
        
        return vessel
    
    def cleanup_old_vessels(self, max_age_minutes: int = 60):
        """
        Remove vessels that haven't been updated recently.
        
        Args:
            max_age_minutes: Maximum age in minutes
        """
        # This would require timestamp parsing - simplified for now
        logger.info(f"Cleanup not yet implemented (max_age: {max_age_minutes}m)")
    
    def close(self):
        """Close service and save data."""
        logger.info("Closing vessel info service...")
        
        # Save all to database
        self.save_all_to_database()
        
        # Close database
        if self.db:
            self.db.close()
        
        logger.info(f"✅ Saved {len(self.vessels_cache)} vessels")

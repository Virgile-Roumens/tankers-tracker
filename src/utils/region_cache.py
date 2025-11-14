"""
Region Caching Layer for Fast Spatial Lookups

Provides optimized region membership checks using bounding box caching
to avoid repeated containment calculations.
"""

from typing import Dict, Set
from collections import defaultdict
import logging

from models.vessel import Vessel
from enums.region import Region
from config import REGIONS

logger = logging.getLogger(__name__)


class RegionCache:
    """
    Efficiently cache which vessels belong to which regions.
    
    This dramatically speeds up region filtering since spatial queries
    are cached rather than recalculated each time.
    """
    
    def __init__(self):
        """Initialize region cache."""
        self.region_vessels: Dict[str, Set[int]] = defaultdict(set)
        self.vessel_regions: Dict[int, Set[str]] = defaultdict(set)
        self._build_region_bounds()
    
    def _build_region_bounds(self):
        """Build cached bounding box data for all regions."""
        self.region_bounds = {}
        for region_name, bounds in REGIONS.items():
            south, west = bounds[0]
            north, east = bounds[1]
            self.region_bounds[region_name] = {
                'south': south,
                'north': north,
                'west': west,
                'east': east
            }
    
    def update_vessel(self, vessel: Vessel) -> None:
        """
        Update vessel position and recalculate region membership.
        
        Args:
            vessel: Vessel to update
        """
        if not vessel.has_position():
            return
        
        mmsi = vessel.mmsi
        
        # Get previous regions
        previous_regions = self.vessel_regions.get(mmsi, set())
        
        # Find current regions
        current_regions = self._find_regions_for_vessel(vessel)
        self.vessel_regions[mmsi] = current_regions
        
        # Update region memberships
        for region in current_regions:
            self.region_vessels[region].add(mmsi)
        
        # Remove from regions no longer in
        for region in previous_regions - current_regions:
            self.region_vessels[region].discard(mmsi)
    
    def _find_regions_for_vessel(self, vessel: Vessel) -> Set[str]:
        """
        Find all regions containing this vessel.
        
        Args:
            vessel: Vessel to locate
            
        Returns:
            Set of region names containing the vessel
        """
        regions = set()
        lat, lon = vessel.lat, vessel.lon
        
        for region_name, bounds in self.region_bounds.items():
            if (bounds['south'] <= lat <= bounds['north'] and
                bounds['west'] <= lon <= bounds['east']):
                regions.add(region_name)
        
        return regions
    
    def get_vessels_in_region(self, region_name: str) -> Set[int]:
        """
        Get all MMSI numbers of vessels in a specific region.
        
        Args:
            region_name: Name of the region
            
        Returns:
            Set of vessel MMSI numbers
        """
        return self.region_vessels.get(region_name, set()).copy()
    
    def get_regions_for_vessel(self, mmsi: int) -> Set[str]:
        """
        Get all regions containing a specific vessel.
        
        Args:
            mmsi: Vessel MMSI number
            
        Returns:
            Set of region names
        """
        return self.vessel_regions.get(mmsi, set()).copy()
    
    def remove_vessel(self, mmsi: int) -> None:
        """
        Remove vessel from cache (e.g., when it's deleted).
        
        Args:
            mmsi: Vessel MMSI to remove
        """
        regions = self.vessel_regions.pop(mmsi, set())
        for region in regions:
            self.region_vessels[region].discard(mmsi)
    
    def get_statistics(self) -> Dict:
        """Get cache statistics."""
        total_vessels = len(self.vessel_regions)
        total_region_entries = sum(len(v) for v in self.region_vessels.values())
        
        return {
            'total_vessels_cached': total_vessels,
            'region_entries': total_region_entries,
            'regions': len(self.region_vessels),
            'avg_vessels_per_region': (
                total_region_entries / len(self.region_vessels) 
                if self.region_vessels else 0
            )
        }
    
    def clear(self) -> None:
        """Clear all cached data."""
        self.region_vessels.clear()
        self.vessel_regions.clear()
        logger.info("Region cache cleared")


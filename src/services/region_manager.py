"""
Region Manager - Centralized region management service

Provides a unified interface for managing tracking regions, filtering vessels,
and handling region-based operations.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from config import REGIONS, PORTS
from models.region import Region, Port
from models.vessel import Vessel

logger = logging.getLogger(__name__)


class RegionManager:
    """
    Centralized service for managing tracking regions.
    
    Features:
    - Dynamic region switching
    - Vessel filtering by region
    - Region statistics and analytics
    - Multi-region support
    - Region persistence
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the region manager.
        
        Args:
            data_dir: Directory for region data and state
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.current_region_file = self.data_dir / "current_region.json"
        self.region_history_file = self.data_dir / "region_history.json"
        
        # Load regions from config
        self.regions: Dict[str, Region] = self._load_regions()
        self.current_region: Optional[str] = self._load_current_region()
        self.region_history: List[Dict] = self._load_region_history()
        
        logger.info(f"RegionManager initialized with {len(self.regions)} regions")
        if self.current_region:
            logger.info(f"Current region: {self.current_region}")
    
    def _load_regions(self) -> Dict[str, Region]:
        """Load regions from configuration."""
        regions = {}
        
        for region_name, bounds in REGIONS.items():
            ports = [
                Port(
                    name=p['name'],
                    lat=p['lat'],
                    lon=p['lon'],
                    country=p['country']
                )
                for p in PORTS.get(region_name, [])
            ]
            
            regions[region_name] = Region(
                name=region_name,
                bounds=bounds,
                ports=ports
            )
        
        return regions
    
    def _load_current_region(self) -> Optional[str]:
        """Load the currently selected region from persistence."""
        try:
            if self.current_region_file.exists():
                with open(self.current_region_file, 'r') as f:
                    data = json.load(f)
                    region = data.get('region')
                    if region in self.regions:
                        return region
        except Exception as e:
            logger.warning(f"Failed to load current region: {e}")
        
        # Default to first available region
        return list(self.regions.keys())[0] if self.regions else None
    
    def _save_current_region(self) -> None:
        """Save the current region to persistence."""
        try:
            data = {
                'region': self.current_region,
                'timestamp': datetime.utcnow().isoformat(),
                'bounds': self.regions[self.current_region].bounds if self.current_region else None
            }
            
            with open(self.current_region_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save current region: {e}")
    
    def _load_region_history(self) -> List[Dict]:
        """Load region switching history."""
        try:
            if self.region_history_file.exists():
                with open(self.region_history_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load region history: {e}")
        
        return []
    
    def _save_region_history(self) -> None:
        """Save region switching history."""
        try:
            with open(self.region_history_file, 'w') as f:
                json.dump(self.region_history[-100:], f, indent=2)  # Keep last 100
        except Exception as e:
            logger.error(f"Failed to save region history: {e}")
    
    def get_region(self, name: str) -> Optional[Region]:
        """
        Get a region by name.
        
        Args:
            name: Region identifier
            
        Returns:
            Region object or None
        """
        return self.regions.get(name)
    
    def get_current_region(self) -> Optional[Region]:
        """Get the currently active region."""
        if self.current_region:
            return self.regions.get(self.current_region)
        return None
    
    def set_current_region(self, region_name: str) -> bool:
        """
        Set the current active region.
        
        Args:
            region_name: Name of region to activate
            
        Returns:
            True if successful
        """
        if region_name not in self.regions:
            logger.error(f"Region '{region_name}' not found")
            return False
        
        old_region = self.current_region
        self.current_region = region_name
        self._save_current_region()
        
        # Track in history
        self.region_history.append({
            'from': old_region,
            'to': region_name,
            'timestamp': datetime.utcnow().isoformat()
        })
        self._save_region_history()
        
        logger.info(f"Region changed: {old_region} → {region_name}")
        return True
    
    def list_regions(self) -> Dict[str, Dict]:
        """
        Get list of all available regions with metadata.
        
        Returns:
            Dictionary of region information
        """
        return {
            name: {
                'bounds': region.bounds,
                'center': region.center,
                'port_count': len(region.ports),
                'is_current': name == self.current_region
            }
            for name, region in self.regions.items()
        }
    
    def filter_vessels_by_region(self, vessels: Dict[int, Vessel], 
                                 region_name: Optional[str] = None) -> Dict[int, Vessel]:
        """
        Filter vessels that are within a specific region.
        
        Args:
            vessels: Dictionary of vessels by MMSI
            region_name: Region to filter by (uses current if None)
            
        Returns:
            Filtered dictionary of vessels
        """
        region_name = region_name or self.current_region
        if not region_name or region_name not in self.regions:
            return vessels
        
        region = self.regions[region_name]
        filtered = {}
        
        for mmsi, vessel in vessels.items():
            if vessel.has_position() and region.contains_point(vessel.lat, vessel.lon):
                filtered[mmsi] = vessel
        
        return filtered
    
    def get_vessels_by_region(self, vessels: Dict[int, Vessel]) -> Dict[str, List[Vessel]]:
        """
        Group vessels by their region.
        
        Args:
            vessels: Dictionary of all vessels
            
        Returns:
            Dictionary mapping region names to vessel lists
        """
        vessels_by_region = {name: [] for name in self.regions.keys()}
        vessels_by_region['unknown'] = []
        
        for vessel in vessels.values():
            if not vessel.has_position():
                continue
            
            found_region = False
            for region_name, region in self.regions.items():
                if region.contains_point(vessel.lat, vessel.lon):
                    vessels_by_region[region_name].append(vessel)
                    found_region = True
                    break
            
            if not found_region:
                vessels_by_region['unknown'].append(vessel)
        
        return vessels_by_region
    
    def get_region_statistics(self, vessels: Dict[int, Vessel]) -> Dict:
        """
        Get comprehensive statistics for each region.
        
        Args:
            vessels: Dictionary of all vessels
            
        Returns:
            Statistics dictionary
        """
        vessels_by_region = self.get_vessels_by_region(vessels)
        
        stats = {}
        for region_name, region_vessels in vessels_by_region.items():
            if region_name == 'unknown':
                continue
                
            tanker_count = sum(1 for v in region_vessels if v.ship_type in range(80, 90))
            cargo_count = sum(1 for v in region_vessels if v.ship_type in range(70, 80))
            
            avg_speed = sum(v.speed for v in region_vessels if v.speed) / len(region_vessels) if region_vessels else 0
            
            stats[region_name] = {
                'total_vessels': len(region_vessels),
                'tankers': tanker_count,
                'cargo': cargo_count,
                'other': len(region_vessels) - tanker_count - cargo_count,
                'avg_speed': round(avg_speed, 1),
                'is_current': region_name == self.current_region
            }
        
        return stats
    
    def get_nearby_ports(self, lat: float, lon: float, 
                        max_distance_km: float = 100) -> List[Tuple[Port, float]]:
        """
        Find ports near a given position.
        
        Args:
            lat: Latitude
            lon: Longitude
            max_distance_km: Maximum distance in kilometers
            
        Returns:
            List of (Port, distance) tuples, sorted by distance
        """
        from math import radians, sin, cos, sqrt, atan2
        
        def haversine_distance(lat1, lon1, lat2, lon2):
            """Calculate distance between two points in km."""
            R = 6371  # Earth radius in km
            
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            
            return R * c
        
        nearby = []
        for region in self.regions.values():
            for port in region.ports:
                distance = haversine_distance(lat, lon, port.lat, port.lon)
                if distance <= max_distance_km:
                    nearby.append((port, distance))
        
        return sorted(nearby, key=lambda x: x[1])
    
    def validate_region(self, region_name: str) -> bool:
        """Check if a region name is valid."""
        return region_name in self.regions
    
    def get_region_bounds(self, region_name: Optional[str] = None) -> List[List[float]]:
        """
        Get bounding box for a region.
        
        Args:
            region_name: Region name (uses current if None)
            
        Returns:
            Bounding box [[south, west], [north, east]]
        """
        region_name = region_name or self.current_region
        if region_name and region_name in self.regions:
            return self.regions[region_name].bounds
        
        # Return worldwide bounds as fallback
        return [[-90, -180], [90, 180]]
    
    def get_region_center(self, region_name: Optional[str] = None) -> Tuple[float, float]:
        """
        Get center point of a region.
        
        Args:
            region_name: Region name (uses current if None)
            
        Returns:
            (latitude, longitude) tuple
        """
        region_name = region_name or self.current_region
        if region_name and region_name in self.regions:
            return self.regions[region_name].center
        
        return (0.0, 0.0)
    
    def export_region_data(self, filepath: str) -> None:
        """
        Export all region data to JSON file.
        
        Args:
            filepath: Output file path
        """
        data = {
            'regions': {},
            'current_region': self.current_region,
            'history': self.region_history
        }
        
        for name, region in self.regions.items():
            data['regions'][name] = {
                'bounds': region.bounds,
                'center': list(region.center),
                'ports': [
                    {
                        'name': p.name,
                        'lat': p.lat,
                        'lon': p.lon,
                        'country': p.country
                    }
                    for p in region.ports
                ]
            }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Region data exported to {filepath}")

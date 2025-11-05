"""
Region data model for geographical tracking areas.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass
class Port:
    """
    Represents a port or terminal.
    
    Attributes:
        name: Port name
        lat: Latitude
        lon: Longitude
        country: Country name with optional flag emoji
    """
    name: str
    lat: float
    lon: float
    country: str


@dataclass
class Region:
    """
    Represents a geographical region for vessel tracking.
    
    Attributes:
        name: Region identifier
        bounds: Bounding box as [[south, west], [north, east]]
        ports: List of ports in the region
    """
    
    name: str
    bounds: List[List[float]]
    ports: List[Port]
    
    @property
    def center(self) -> Tuple[float, float]:
        """Calculate center point of region."""
        south_west, north_east = self.bounds
        center_lat = (south_west[0] + north_east[0]) / 2
        center_lon = (south_west[1] + north_east[1]) / 2
        return (center_lat, center_lon)
    
    @property
    def bounding_box(self) -> List[List[float]]:
        """Get bounding box for AIS subscription."""
        return self.bounds
    
    def contains_point(self, lat: float, lon: float) -> bool:
        """
        Check if a point is within the region bounds.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            True if point is within bounds
        """
        south_west, north_east = self.bounds
        return (south_west[0] <= lat <= north_east[0] and
                south_west[1] <= lon <= north_east[1])
    
    def __str__(self) -> str:
        """String representation of region."""
        return f"Region({self.name}) with {len(self.ports)} ports"

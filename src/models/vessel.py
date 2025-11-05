"""
Vessel data model for representing tracked ships.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Vessel:
    """
    Represents a tracked vessel with AIS data.
    
    Attributes:
        mmsi: Maritime Mobile Service Identity (unique vessel ID)
        lat: Current latitude
        lon: Current longitude
        name: Vessel name
        speed: Speed over ground in knots
        course: Course over ground in degrees
        destination: Destination port
        ship_type: IMO ship type code
        last_update: Timestamp of last position update
    """
    
    mmsi: int
    lat: Optional[float] = None
    lon: Optional[float] = None
    name: Optional[str] = None
    speed: Optional[float] = None
    course: Optional[float] = None
    destination: Optional[str] = None
    ship_type: Optional[int] = None
    last_update: Optional[str] = None
    
    def update_position(self, lat: float, lon: float, speed: Optional[float] = None, 
                       course: Optional[float] = None, timestamp: Optional[str] = None) -> None:
        """
        Update vessel position data.
        
        Args:
            lat: New latitude
            lon: New longitude
            speed: Speed over ground in knots
            course: Course over ground in degrees
            timestamp: Update timestamp
        """
        self.lat = lat
        self.lon = lon
        if speed is not None:
            self.speed = round(speed, 1)
        if course is not None:
            self.course = round(course, 1)
        self.last_update = timestamp or datetime.utcnow().strftime("%H:%M:%S")
    
    def update_static_data(self, name: Optional[str] = None, 
                          destination: Optional[str] = None,
                          ship_type: Optional[int] = None) -> None:
        """
        Update vessel static information.
        
        Args:
            name: Vessel name
            destination: Destination port
            ship_type: IMO ship type code
        """
        if name:
            self.name = name.strip()
        if destination:
            self.destination = destination.strip()
        if ship_type is not None:
            self.ship_type = ship_type
    
    def has_position(self) -> bool:
        """Check if vessel has valid position data."""
        return self.lat is not None and self.lon is not None
    
    def is_tanker(self, tanker_types: list) -> bool:
        """Check if vessel is a tanker type."""
        return self.ship_type in tanker_types if self.ship_type else False
    
    def to_dict(self) -> dict:
        """Convert vessel to dictionary representation."""
        return {
            "mmsi": self.mmsi,
            "lat": self.lat,
            "lon": self.lon,
            "name": self.name,
            "speed": self.speed,
            "course": self.course,
            "destination": self.destination,
            "ship_type": self.ship_type,
            "last_update": self.last_update
        }
    
    def __str__(self) -> str:
        """String representation of vessel."""
        return f"Vessel({self.name or self.mmsi}) at ({self.lat}, {self.lon})"

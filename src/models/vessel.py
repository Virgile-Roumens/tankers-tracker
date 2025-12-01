"""
Vessel data model for representing tracked ships.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Union

from enums.ship_type import ShipType
from enums.navigational_status import NavigationalStatus


@dataclass
class Vessel:
    """
    Represents a tracked vessel with comprehensive AIS data.
    
    Attributes:
        mmsi: Maritime Mobile Service Identity (unique vessel ID)
        
        # Position Data
        lat: Current latitude
        lon: Current longitude
        speed: Speed over ground in knots
        course: Course over ground in degrees
        heading: True heading in degrees
        rot: Rate of turn
        navigational_status: Navigation status code (0-15)
        position_accuracy: Position accuracy (0=low >10m, 1=high <10m)
        
        # Static Vessel Data
        name: Vessel name
        imo: IMO number (International Maritime Organization)
        callsign: Radio callsign
        ship_type: IMO ship type code
        
        # Dimensions (in meters)
        length: Length overall
        width: Beam (width)
        draught: Current draught (depth in water)
        dimension_to_bow: Distance from GPS to bow
        dimension_to_stern: Distance from GPS to stern
        dimension_to_port: Distance from GPS to port side
        dimension_to_starboard: Distance from GPS to starboard side
        
        # Voyage Data
        destination: Destination port
        eta: Estimated time of arrival (timestamp)
        cargo: Cargo type/description
        deadweight: Deadweight tonnage (DWT)
        gross_tonnage: Gross tonnage (GT)
        
        # Tracking Metadata
        last_update: Timestamp of last position update
        first_seen: Timestamp when vessel was first detected
        update_count: Number of position updates received
    """
    
    mmsi: int
    
    # Position Data
    lat: Optional[float] = None
    lon: Optional[float] = None
    speed: Optional[float] = None
    course: Optional[float] = None
    heading: Optional[int] = None
    rot: Optional[float] = None
    navigational_status: Optional[NavigationalStatus] = None
    position_accuracy: Optional[int] = None
    
    # Static Vessel Data
    name: Optional[str] = None
    imo: Optional[int] = None
    callsign: Optional[str] = None
    ship_type: Optional[ShipType] = None
    
    # Dimensions
    length: Optional[float] = None
    width: Optional[float] = None
    draught: Optional[float] = None
    dimension_to_bow: Optional[int] = None
    dimension_to_stern: Optional[int] = None
    dimension_to_port: Optional[int] = None
    dimension_to_starboard: Optional[int] = None
    
    # Voyage Data
    destination: Optional[str] = None
    eta: Optional[str] = None
    cargo: Optional[str] = None
    deadweight: Optional[int] = None
    gross_tonnage: Optional[int] = None
    
    # Tracking Metadata
    last_update: Optional[str] = None
    first_seen: Optional[str] = None
    update_count: int = 0
    
    def update_position(self, lat: float, lon: float, speed: Optional[float] = None, 
                       course: Optional[float] = None, heading: Optional[int] = None,
                       rot: Optional[float] = None, navigational_status: Optional[Union[int, NavigationalStatus]] = None,
                       position_accuracy: Optional[int] = None, timestamp: Optional[str] = None) -> None:
        """
        Update vessel position data.
        
        Args:
            lat: New latitude
            lon: New longitude
            speed: Speed over ground in knots
            course: Course over ground in degrees
            heading: True heading in degrees
            rot: Rate of turn
            navigational_status: Navigation status code
            position_accuracy: GPS accuracy indicator
            timestamp: Update timestamp
        """
        self.lat = lat
        self.lon = lon
        if speed is not None:
            self.speed = round(speed, 1)
        if course is not None:
            self.course = round(course, 1)
        if heading is not None:
            self.heading = heading
        if rot is not None:
            self.rot = round(rot, 2)
        if navigational_status is not None:
            # Convert int to NavigationalStatus enum if needed
            if isinstance(navigational_status, int):
                self.navigational_status = NavigationalStatus.from_code(navigational_status)
            else:
                self.navigational_status = navigational_status
        if position_accuracy is not None:
            self.position_accuracy = position_accuracy
        
        self.last_update = timestamp or datetime.utcnow().strftime("%H:%M:%S")
        self.update_count += 1
        
        if self.first_seen is None:
            self.first_seen = self.last_update
    
    def update_static_data(self, name: Optional[str] = None, 
                          destination: Optional[str] = None,
                          ship_type: Optional[Union[int, ShipType]] = None,
                          imo: Optional[int] = None,
                          callsign: Optional[str] = None,
                          length: Optional[float] = None,
                          width: Optional[float] = None,
                          draught: Optional[float] = None,
                          dimension_to_bow: Optional[int] = None,
                          dimension_to_stern: Optional[int] = None,
                          dimension_to_port: Optional[int] = None,
                          dimension_to_starboard: Optional[int] = None,
                          eta: Optional[str] = None) -> None:
        """
        Update vessel static information.
        
        Args:
            name: Vessel name
            destination: Destination port
            ship_type: IMO ship type code (int) or ShipType enum
            imo: IMO number
            callsign: Radio callsign
            length: Length overall
            width: Beam (width)
            draught: Current draught
            dimension_to_bow: Distance to bow
            dimension_to_stern: Distance to stern
            dimension_to_port: Distance to port
            dimension_to_starboard: Distance to starboard
            eta: Estimated time of arrival
        """
        if name:
            self.name = name.strip()
        if destination:
            self.destination = destination.strip()
        if ship_type is not None:
            # Convert int to ShipType enum if needed
            if isinstance(ship_type, int):
                self.ship_type = ShipType.from_code(ship_type)
            else:
                self.ship_type = ship_type
        if imo is not None:
            self.imo = imo
        if callsign:
            self.callsign = callsign.strip()
        if length is not None:
            self.length = length
        if width is not None:
            self.width = width
        if draught is not None:
            self.draught = round(draught, 1)
        if dimension_to_bow is not None:
            self.dimension_to_bow = dimension_to_bow
        if dimension_to_stern is not None:
            self.dimension_to_stern = dimension_to_stern
        if dimension_to_port is not None:
            self.dimension_to_port = dimension_to_port
        if dimension_to_starboard is not None:
            self.dimension_to_starboard = dimension_to_starboard
        if eta:
            self.eta = eta
    
    def has_position(self) -> bool:
        """Check if vessel has valid position data."""
        return self.lat is not None and self.lon is not None
    
    def is_tanker(self) -> bool:
        """
        Check if vessel is a tanker type.
        
        Returns:
            bool: True if vessel is a tanker (IMO codes 80-89), False otherwise
        """
        return self.ship_type.is_tanker() if self.ship_type else False
    
    def get_ship_type_name(self) -> str:
        """
        Get human-readable ship type name.
        
        Returns:
            str: Display name for ship type, or "Unknown" if not set
        """
        return self.ship_type.display_name if self.ship_type else "Unknown"
    
    def get_dimensions(self) -> str:
        """Get formatted vessel dimensions."""
        if self.length and self.width:
            return f"{self.length:.0f}m × {self.width:.0f}m"
        return "Unknown"
    
    def get_navigational_status_text(self) -> str:
        """
        Get human-readable navigation status.
        
        Returns:
            str: Display name for navigational status, or "Unknown" if not set
        """
        return self.navigational_status.display_name if self.navigational_status else "Unknown"
    
    def to_dict(self) -> dict:
        """Convert vessel to dictionary representation."""
        return {
            "mmsi": self.mmsi,
            "lat": self.lat,
            "lon": self.lon,
            "name": self.name,
            "imo": self.imo,
            "callsign": self.callsign,
            "speed": self.speed,
            "course": self.course,
            "heading": self.heading,
            "rot": self.rot,
            "navigational_status": self.navigational_status.value if self.navigational_status else None,
            "destination": self.destination,
            "eta": self.eta,
            "ship_type": self.ship_type.value if self.ship_type else None,
            "length": self.length,
            "width": self.width,
            "draught": self.draught,
            "cargo": self.cargo,
            "deadweight": self.deadweight,
            "gross_tonnage": self.gross_tonnage,
            "last_update": self.last_update,
            "first_seen": self.first_seen,
            "update_count": self.update_count
        }
    
    def __str__(self) -> str:
        """String representation of vessel."""
        return f"Vessel({self.name or self.mmsi}) at ({self.lat}, {self.lon})"

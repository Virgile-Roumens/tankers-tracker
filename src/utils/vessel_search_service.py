"""
Vessel search service for finding vessels by name, MMSI, and other criteria.
"""

import logging
from typing import List, Optional, Dict
from models.vessel import Vessel
from enums.ship_type import ShipType

logger = logging.getLogger(__name__)


class VesselSearchService:
    """Service for searching and filtering vessels."""
    
    def __init__(self, vessels_dict: Dict[int, Vessel]):
        """Initialize with vessels dictionary."""
        self.vessels_dict = vessels_dict
    
    def search_by_name(self, name: str, partial: bool = True) -> List[Vessel]:
        """
        Search vessels by name.
        
        Args:
            name: Vessel name to search for
            partial: If True, find partial matches; if False, exact match
            
        Returns:
            List of matching Vessel objects
        """
        search_term = name.lower()
        results = []
        
        for vessel in self.vessels_dict.values():
            if vessel.name:
                vessel_name = vessel.name.lower()
                if partial:
                    if search_term in vessel_name:
                        results.append(vessel)
                elif vessel_name == search_term:
                    results.append(vessel)
        
        return sorted(results, key=lambda v: v.name or "")
    
    def search_by_mmsi(self, mmsi: int) -> Optional[Vessel]:
        """
        Search vessel by MMSI (Maritime Mobile Service Identity).
        
        Args:
            mmsi:MMSI number
            
        Returns:
            Vessel if found, None otherwise
        """
        return self.vessels_dict.get(mmsi)
    
    def search_by_callsign(self, callsign: str) -> Optional[Vessel]:
        """Search vessel by radio callsign."""
        for vessel in self.vessels_dict.values():
            if vessel.callsign and vessel.callsign.upper() == callsign.upper():
                return vessel
        return None
    
    def search_by_imo(self, imo: int) -> Optional[Vessel]:
        """Search vessel by IMO number."""
        for vessel in self.vessels_dict.values():
            if vessel.imo == imo:
                return vessel
        return None
    
    def search_by_destination(self, destination: str, partial: bool = True) -> List[Vessel]:
        """Search vessels by destination port."""
        search_term = destination.lower()
        results = []
        
        for vessel in self.vessels_dict.values():
            if vessel.destination:
                dest_name = vessel.destination.lower()
                if partial:
                    if search_term in dest_name:
                        results.append(vessel)
                elif dest_name == search_term:
                    results.append(vessel)
        
        return results
    
    def get_unknown_vessels(self) -> List[Vessel]:
        """Get all vessels with unknown ship type."""
        return [v for v in self.vessels_dict.values() if v.ship_type is None]
    
    def get_vessels_by_type(self, ship_type: ShipType) -> List[Vessel]:
        """Get all vessels of a specific type."""
        return [v for v in self.vessels_dict.values() if v.ship_type == ship_type]
    
    def get_unclassified_vessels(self) -> List[Vessel]:
        """Get vessels without position data."""
        return [v for v in self.vessels_dict.values() if not v.has_position()]
    
    def get_stationary_vessels(self, speed_threshold: float = 0.5) -> List[Vessel]:
        """Get vessels below speed threshold (stationary/anchored)."""
        return [v for v in self.vessels_dict.values() 
                if v.has_position() and (v.speed is None or v.speed <= speed_threshold)]
    
    def get_fast_moving_vessels(self, speed_threshold: float = 10.0) -> List[Vessel]:
        """Get vessels above speed threshold (moving fast)."""
        return [v for v in self.vessels_dict.values() 
                if v.has_position() and v.speed and v.speed >= speed_threshold]


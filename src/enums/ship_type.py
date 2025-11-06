"""
Ship Type Enum for IMO ship type codes.

This module defines the ShipType enum which provides type-safe ship type definitions
based on IMO standards, with special focus on tankers and cargo vessels.
"""

from enum import IntEnum
from typing import Optional, Set


class ShipType(IntEnum):
    """
    IMO ship type codes for tankers and cargo vessels.
    
    The values 70-89 represent various types of cargo and tanker vessels,
    with specific codes for hazardous cargo classifications.
    
    Attributes:
        CARGO: General cargo vessel (70)
        CARGO_HAZARDOUS_A: Cargo vessel carrying hazardous category A materials (71)
        CARGO_HAZARDOUS_B: Cargo vessel carrying hazardous category B materials (72)
        CARGO_HAZARDOUS_C: Cargo vessel carrying hazardous category C materials (73)
        CARGO_HAZARDOUS_D: Cargo vessel carrying hazardous category D materials (74)
        TANKER: General tanker vessel (80)
        TANKER_HAZARDOUS_A: Tanker carrying hazardous category A materials (81)
        TANKER_HAZARDOUS_B: Tanker carrying hazardous category B materials (82)
        TANKER_HAZARDOUS_C: Tanker carrying hazardous category C materials (83)
        TANKER_HAZARDOUS_D: Tanker carrying hazardous category D materials (84)
    """
    
    # Cargo vessels (70-79)
    CARGO = 70
    CARGO_HAZARDOUS_A = 71
    CARGO_HAZARDOUS_B = 72
    CARGO_HAZARDOUS_C = 73
    CARGO_HAZARDOUS_D = 74
    
    # Tankers (80-89)
    TANKER = 80
    TANKER_HAZARDOUS_A = 81
    TANKER_HAZARDOUS_B = 82
    TANKER_HAZARDOUS_C = 83
    TANKER_HAZARDOUS_D = 84
    
    @property
    def display_name(self) -> str:
        """
        Get human-readable display name for this ship type.
        
        Returns:
            str: Human-readable ship type name
        """
        return _SHIP_TYPE_NAMES[self]
    
    def is_tanker(self) -> bool:
        """
        Check if this ship type is a tanker.
        
        Tankers are classified as IMO codes 80-89 (inclusive).
        
        Returns:
            bool: True if this is a tanker type, False otherwise
        """
        return 80 <= self.value <= 89
    
    def is_hazardous(self) -> bool:
        """
        Check if this ship type carries hazardous materials.
        
        Returns:
            bool: True if carrying hazardous cargo (categories A-D)
        """
        return self in {
            ShipType.CARGO_HAZARDOUS_A,
            ShipType.CARGO_HAZARDOUS_B,
            ShipType.CARGO_HAZARDOUS_C,
            ShipType.CARGO_HAZARDOUS_D,
            ShipType.TANKER_HAZARDOUS_A,
            ShipType.TANKER_HAZARDOUS_B,
            ShipType.TANKER_HAZARDOUS_C,
            ShipType.TANKER_HAZARDOUS_D,
        }
    
    def is_cargo(self) -> bool:
        """
        Check if this ship type is a cargo vessel (not tanker).
        
        Returns:
            bool: True if this is a cargo vessel (70-79)
        """
        return 70 <= self.value <= 79
    
    @classmethod
    def from_code(cls, code: Optional[int]) -> Optional['ShipType']:
        """
        Convert an IMO ship type code to a ShipType enum.
        
        Args:
            code: IMO ship type code (integer)
            
        Returns:
            ShipType enum if code is valid, None otherwise
        """
        if code is None:
            return None
        try:
            return cls(code)
        except ValueError:
            return None
    
    def get_color(self) -> str:
        """
        Get the color for this ship type for map display.
        
        Returns:
            str: Hex color code for the ship type
        """
        if self.is_tanker():
            if self.is_hazardous():
                return '#8B0000'  # Dark red for hazardous tankers
            return '#DC143C'  # Crimson for regular tankers
        elif self.is_cargo():
            if self.is_hazardous():
                return '#FF6347'  # Tomato red for hazardous cargo
            return '#FF8C00'  # Dark orange for regular cargo
        else:
            return '#4169E1'  # Royal blue for other vessels
    
    @classmethod
    def all_tanker_types(cls) -> Set['ShipType']:
        """
        Get all ship types that are tankers.
        
        Returns:
            Set of ShipType enums representing tankers
        """
        return {ship_type for ship_type in cls if ship_type.is_tanker()}
    
    @classmethod
    def all_cargo_types(cls) -> Set['ShipType']:
        """
        Get all ship types that are cargo vessels.
        
        Returns:
            Set of ShipType enums representing cargo vessels
        """
        return {ship_type for ship_type in cls if ship_type.is_cargo()}
    
    @classmethod
    def all_hazardous_types(cls) -> Set['ShipType']:
        """
        Get all ship types that carry hazardous materials.
        
        Returns:
            Set of ShipType enums representing hazardous cargo vessels
        """
        return {ship_type for ship_type in cls if ship_type.is_hazardous()}


# Display names mapping
_SHIP_TYPE_NAMES = {
    ShipType.CARGO: "Cargo",
    ShipType.CARGO_HAZARDOUS_A: "Cargo - Hazardous A",
    ShipType.CARGO_HAZARDOUS_B: "Cargo - Hazardous B",
    ShipType.CARGO_HAZARDOUS_C: "Cargo - Hazardous C",
    ShipType.CARGO_HAZARDOUS_D: "Cargo - Hazardous D",
    ShipType.TANKER: "Tanker",
    ShipType.TANKER_HAZARDOUS_A: "Tanker - Hazardous A",
    ShipType.TANKER_HAZARDOUS_B: "Tanker - Hazardous B",
    ShipType.TANKER_HAZARDOUS_C: "Tanker - Hazardous C",
    ShipType.TANKER_HAZARDOUS_D: "Tanker - Hazardous D",
}


# Convenience constants
CARGO_CODES = list(range(70, 80))   # Cargo vessels: IMO codes 70-79
TANKER_CODES = list(range(80, 90))  # Tankers: IMO codes 80-89


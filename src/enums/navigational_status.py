"""
Navigational Status Enum for AIS navigational status codes.

This module defines the NavigationalStatus enum which provides type-safe
navigational status definitions based on AIS standards.
"""

from enum import IntEnum
from typing import Optional


class NavigationalStatus(IntEnum):
    """
    AIS navigational status codes (0-15).
    
    These codes indicate the current operational status of a vessel
    as reported by its AIS transponder.
    
    Attributes:
        UNDER_WAY_ENGINE: Vessel is moving under engine power (0)
        AT_ANCHOR: Vessel is anchored (1)
        NOT_UNDER_COMMAND: Vessel cannot be controlled (2)
        RESTRICTED_MANOEUVRABILITY: Limited ability to maneuver (3)
        CONSTRAINED_BY_DRAUGHT: Limited by water depth (4)
        MOORED: Vessel is moored to dock/buoy (5)
        AGROUND: Vessel is aground (6)
        ENGAGED_IN_FISHING: Actively fishing (7)
        UNDER_WAY_SAILING: Moving under sail power (8)
        RESERVED_HSC: Reserved for high-speed craft (9)
        RESERVED_WIG: Reserved for wing-in-ground craft (10)
        RESERVED_11: Reserved for future use (11)
        RESERVED_12: Reserved for future use (12)
        RESERVED_13: Reserved for future use (13)
        AIS_SART: AIS Search and Rescue Transmitter (14)
        NOT_DEFINED: Status not defined/default (15)
    """
    
    # Active navigation statuses
    UNDER_WAY_ENGINE = 0
    AT_ANCHOR = 1
    NOT_UNDER_COMMAND = 2
    RESTRICTED_MANOEUVRABILITY = 3
    CONSTRAINED_BY_DRAUGHT = 4
    MOORED = 5
    AGROUND = 6
    ENGAGED_IN_FISHING = 7
    UNDER_WAY_SAILING = 8
    
    # Reserved statuses
    RESERVED_HSC = 9
    RESERVED_WIG = 10
    RESERVED_11 = 11
    RESERVED_12 = 12
    RESERVED_13 = 13
    
    # Special statuses
    AIS_SART = 14
    NOT_DEFINED = 15
    
    @property
    def display_name(self) -> str:
        """
        Get human-readable display name for this navigational status.
        
        Returns:
            str: Human-readable status name
        """
        return _STATUS_NAMES[self]
    
    def get_color(self) -> str:
        """
        Get the color for this navigational status for display.
        
        Returns:
            str: Hex color code for the status
        """
        return _STATUS_COLORS.get(self, '#9E9E9E')
    
    def is_underway(self) -> bool:
        """
        Check if vessel is currently underway (moving).
        
        Returns:
            bool: True if vessel is underway
        """
        return self in {
            NavigationalStatus.UNDER_WAY_ENGINE,
            NavigationalStatus.UNDER_WAY_SAILING
        }
    
    def is_stationary(self) -> bool:
        """
        Check if vessel is stationary (not moving).
        
        Returns:
            bool: True if vessel is stationary
        """
        return self in {
            NavigationalStatus.AT_ANCHOR,
            NavigationalStatus.MOORED,
            NavigationalStatus.AGROUND
        }
    
    def is_restricted(self) -> bool:
        """
        Check if vessel has restricted movement capability.
        
        Returns:
            bool: True if vessel is restricted
        """
        return self in {
            NavigationalStatus.NOT_UNDER_COMMAND,
            NavigationalStatus.RESTRICTED_MANOEUVRABILITY,
            NavigationalStatus.CONSTRAINED_BY_DRAUGHT
        }
    
    def is_emergency(self) -> bool:
        """
        Check if this is an emergency status.
        
        Returns:
            bool: True if emergency status
        """
        return self in {
            NavigationalStatus.NOT_UNDER_COMMAND,
            NavigationalStatus.AGROUND,
            NavigationalStatus.AIS_SART
        }
    
    @classmethod
    def from_code(cls, code: Optional[int]) -> Optional['NavigationalStatus']:
        """
        Convert an AIS navigational status code to a NavigationalStatus enum.
        
        Args:
            code: AIS navigational status code (integer 0-15)
            
        Returns:
            NavigationalStatus enum if code is valid, None otherwise
        """
        if code is None:
            return None
        try:
            return cls(code)
        except ValueError:
            return None


# Display names mapping
_STATUS_NAMES = {
    NavigationalStatus.UNDER_WAY_ENGINE: "Under way using engine",
    NavigationalStatus.AT_ANCHOR: "At anchor",
    NavigationalStatus.NOT_UNDER_COMMAND: "Not under command",
    NavigationalStatus.RESTRICTED_MANOEUVRABILITY: "Restricted manoeuvrability",
    NavigationalStatus.CONSTRAINED_BY_DRAUGHT: "Constrained by draught",
    NavigationalStatus.MOORED: "Moored",
    NavigationalStatus.AGROUND: "Aground",
    NavigationalStatus.ENGAGED_IN_FISHING: "Engaged in fishing",
    NavigationalStatus.UNDER_WAY_SAILING: "Under way sailing",
    NavigationalStatus.RESERVED_HSC: "Reserved for HSC",
    NavigationalStatus.RESERVED_WIG: "Reserved for WIG",
    NavigationalStatus.RESERVED_11: "Reserved",
    NavigationalStatus.RESERVED_12: "Reserved",
    NavigationalStatus.RESERVED_13: "Reserved",
    NavigationalStatus.AIS_SART: "AIS-SART",
    NavigationalStatus.NOT_DEFINED: "Not defined",
}

# Color mapping for different statuses
_STATUS_COLORS = {
    NavigationalStatus.UNDER_WAY_ENGINE: '#4CAF50',      # Green - moving
    NavigationalStatus.UNDER_WAY_SAILING: '#4CAF50',     # Green - moving
    NavigationalStatus.AT_ANCHOR: '#FF9800',             # Orange - anchored
    NavigationalStatus.MOORED: '#2196F3',                # Blue - moored
    NavigationalStatus.ENGAGED_IN_FISHING: '#00BCD4',    # Cyan - fishing
    NavigationalStatus.CONSTRAINED_BY_DRAUGHT: '#FF5722', # Deep orange - constrained
    NavigationalStatus.NOT_UNDER_COMMAND: '#F44336',     # Red - emergency
    NavigationalStatus.RESTRICTED_MANOEUVRABILITY: '#F44336', # Red - emergency
    NavigationalStatus.AGROUND: '#F44336',               # Red - emergency
    NavigationalStatus.AIS_SART: '#F44336',              # Red - emergency
    NavigationalStatus.NOT_DEFINED: '#9E9E9E',           # Gray - unknown
}



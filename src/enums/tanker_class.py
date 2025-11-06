"""
Tanker Class Enum for tanker size classifications.

This module defines the TankerClass enum which categorizes tankers
by deadweight tonnage (DWT) for operational and regulatory purposes.
"""

from enum import Enum
from typing import Optional


class TankerClass(Enum):
    """
    Tanker size classifications by deadweight tonnage.
    
    These classifications are widely used in maritime industry for:
    - Regulatory compliance
    - Canal transit requirements
    - Operational planning
    - Market analysis
    
    Attributes:
        ULCC: Ultra Large Crude Carrier (320,000+ DWT)
        VLCC: Very Large Crude Carrier (200,000-320,000 DWT)
        SUEZMAX: Maximum size for Suez Canal (120,000-200,000 DWT)
        AFRAMAX: Average Freight Rate Assessment (80,000-120,000 DWT)
        PANAMAX: Maximum size for Panama Canal (60,000-80,000 DWT)
        HANDYMAX: Handy maximum (40,000-60,000 DWT)
        HANDYSIZE: Handy size (10,000-40,000 DWT)
        SMALL: Small tanker (<10,000 DWT)
    """
    
    ULCC = "ulcc"
    VLCC = "vlcc"
    SUEZMAX = "suezmax"
    AFRAMAX = "aframax"
    PANAMAX = "panamax"
    HANDYMAX = "handymax"
    HANDYSIZE = "handysize"
    SMALL = "small"
    
    @property
    def display_name(self) -> str:
        """
        Get human-readable display name.
        
        Returns:
            str: Full name with description
        """
        return _TANKER_CLASS_NAMES[self]
    
    @property
    def description(self) -> str:
        """
        Get detailed description of the tanker class.
        
        Returns:
            str: Description with key characteristics
        """
        return _TANKER_CLASS_DESCRIPTIONS[self]
    
    @property
    def min_dwt(self) -> float:
        """Get minimum deadweight tonnage for this class."""
        min_val, _ = _TANKER_CLASS_RANGES[self]
        return min_val
    
    @property
    def max_dwt(self) -> float:
        """Get maximum deadweight tonnage for this class."""
        _, max_val = _TANKER_CLASS_RANGES[self]
        return max_val
    
    def __str__(self) -> str:
        """Return formatted string representation."""
        return f"{self.display_name} ({self.min_dwt:,.0f}-{self.max_dwt:,.0f} DWT)"
    
    @classmethod
    def classify(cls, deadweight_tonnage: Optional[float]) -> Optional['TankerClass']:
        """
        Classify a tanker by its deadweight tonnage.
        
        Args:
            deadweight_tonnage: Vessel's DWT
            
        Returns:
            TankerClass enum if DWT falls within a range, None otherwise
        """
        if deadweight_tonnage is None or deadweight_tonnage < 0:
            return None
        
        # Check each class range
        for tanker_class in cls:
            min_dwt, max_dwt = _TANKER_CLASS_RANGES[tanker_class]
            if min_dwt <= deadweight_tonnage < max_dwt:
                return tanker_class
        
        return None
    
    @classmethod
    def from_string(cls, class_str: Optional[str]) -> Optional['TankerClass']:
        """
        Convert a string to a TankerClass enum.
        
        Args:
            class_str: Tanker class name as string
            
        Returns:
            TankerClass enum if valid, None otherwise
        """
        if class_str is None:
            return None
        
        try:
            return cls(class_str.lower())
        except ValueError:
            return None
    
    @classmethod
    def large_carriers(cls) -> list['TankerClass']:
        """
        Get all large tanker classes (ULCC, VLCC, Suezmax).
        
        Returns:
            List of large tanker classes
        """
        return [cls.ULCC, cls.VLCC, cls.SUEZMAX]
    
    @classmethod
    def medium_carriers(cls) -> list['TankerClass']:
        """
        Get all medium tanker classes (Aframax, Panamax).
        
        Returns:
            List of medium tanker classes
        """
        return [cls.AFRAMAX, cls.PANAMAX]
    
    @classmethod
    def small_carriers(cls) -> list['TankerClass']:
        """
        Get all small tanker classes (Handymax, Handysize, Small).
        
        Returns:
            List of small tanker classes
        """
        return [cls.HANDYMAX, cls.HANDYSIZE, cls.SMALL]


# Display names
_TANKER_CLASS_NAMES = {
    TankerClass.ULCC: "Ultra Large Crude Carrier (ULCC)",
    TankerClass.VLCC: "Very Large Crude Carrier (VLCC)",
    TankerClass.SUEZMAX: "Suezmax",
    TankerClass.AFRAMAX: "Aframax",
    TankerClass.PANAMAX: "Panamax",
    TankerClass.HANDYMAX: "Handymax",
    TankerClass.HANDYSIZE: "Handysize",
    TankerClass.SMALL: "Small Tanker",
}

# Detailed descriptions
_TANKER_CLASS_DESCRIPTIONS = {
    TankerClass.ULCC: "Largest tankers, designed for long-distance crude oil transport. Cannot transit through Suez or Panama canals.",
    TankerClass.VLCC: "Very large crude carriers. Cannot transit through Suez or Panama canals. Most economical for long-haul routes.",
    TankerClass.SUEZMAX: "Maximum size that can transit the Suez Canal. Optimal for Middle East to Europe routes.",
    TankerClass.AFRAMAX: "Average Freight Rate Assessment. Flexible vessels used on various routes including all major canals.",
    TankerClass.PANAMAX: "Maximum size for Panama Canal transit. Widely used for Americas routes.",
    TankerClass.HANDYMAX: "Handy maximum. Versatile vessels with good cargo flexibility.",
    TankerClass.HANDYSIZE: "Handy size. Smaller tankers for regional and specialized trades.",
    TankerClass.SMALL: "Small tankers for coastal trade and specialized cargoes.",
}

# DWT ranges for classification
_TANKER_CLASS_RANGES = {
    TankerClass.ULCC: (320000, float('inf')),
    TankerClass.VLCC: (200000, 320000),
    TankerClass.SUEZMAX: (120000, 200000),
    TankerClass.AFRAMAX: (80000, 120000),
    TankerClass.PANAMAX: (60000, 80000),
    TankerClass.HANDYMAX: (40000, 60000),
    TankerClass.HANDYSIZE: (10000, 40000),
    TankerClass.SMALL: (0, 10000),
}



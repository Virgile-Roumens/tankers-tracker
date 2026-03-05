"""
Bulk Carrier Class Enum for dry bulk carrier size classifications.

This module defines the BulkCarrierClass enum which categorizes dry bulk carriers
by deadweight tonnage (DWT) and vessel dimensions, following standard industry
classifications used in commodity trading and maritime operations.

Classifications:
    - Capesize:   100,000+ DWT (Iron ore, Coal - long haul)
    - Panamax:    65,000-100,000 DWT (Coal, Grain, Iron ore)
    - Supramax:   50,000-65,000 DWT (Grain, Sugar, Cement, Fertilizer)
    - Handymax:   40,000-50,000 DWT (Grain, Steel, Forest products)
    - Handysize:  15,000-40,000 DWT (Minor bulk, Steel, Grain)
    - Small:      < 15,000 DWT (Coastal bulk, Aggregates)
"""

from enum import Enum
from typing import Optional


class BulkCarrierClass(Enum):
    """
    Classification of dry bulk carriers by size (DWT - Deadweight Tonnage).
    
    Standard industry classifications widely used in:
    - Freight rate assessment (Baltic Dry Index segments)
    - Commodity trading and shipping logistics
    - Canal transit requirements
    - Port capacity planning
    """
    
    CAPESIZE = "capesize"
    PANAMAX = "panamax"
    SUPRAMAX = "supramax"
    HANDYMAX = "handymax"
    HANDYSIZE = "handysize"
    SMALL = "small"

    @property
    def display_name(self) -> str:
        """Get human-readable display name."""
        return _BULK_CLASS_NAMES[self]

    @property
    def description(self) -> str:
        """Get detailed description of the bulk carrier class."""
        return _BULK_CLASS_DESCRIPTIONS[self]

    @property
    def min_dwt(self) -> float:
        """Get minimum deadweight tonnage for this class."""
        min_val, _ = _BULK_CLASS_RANGES[self]
        return min_val

    @property
    def max_dwt(self) -> float:
        """Get maximum deadweight tonnage for this class."""
        _, max_val = _BULK_CLASS_RANGES[self]
        return max_val

    @property
    def dwt_range_str(self) -> str:
        """Get the DWT range description for this class."""
        min_val, max_val = _BULK_CLASS_RANGES[self]
        if max_val == float('inf'):
            return f"{min_val:,.0f}+ DWT"
        return f"{min_val:,.0f}-{max_val:,.0f} DWT"

    @property
    def typical_cargo(self) -> str:
        """Get typical cargo description for this class."""
        return _BULK_CLASS_CARGOES[self]

    @property
    def color(self) -> str:
        """Get display color for this bulk carrier class on maps."""
        return _BULK_CLASS_COLORS[self]

    def __str__(self) -> str:
        """Return formatted string representation."""
        return f"{self.display_name} ({self.dwt_range_str})"

    @classmethod
    def classify(cls, deadweight_tonnage: Optional[float]) -> Optional['BulkCarrierClass']:
        """
        Classify a bulk carrier by its deadweight tonnage.
        
        Args:
            deadweight_tonnage: Vessel's DWT
            
        Returns:
            BulkCarrierClass enum if DWT falls within a range, None otherwise
        """
        if deadweight_tonnage is None or deadweight_tonnage < 0:
            return None
        
        for bulk_class in cls:
            min_dwt, max_dwt = _BULK_CLASS_RANGES[bulk_class]
            if min_dwt <= deadweight_tonnage < max_dwt:
                return bulk_class
        
        return None

    @classmethod
    def classify_by_dimensions(cls, length: Optional[float], 
                                width: Optional[float] = None) -> Optional['BulkCarrierClass']:
        """
        Approximate bulk carrier class from vessel dimensions when DWT is unavailable.
        
        This is a heuristic based on typical vessel dimensions:
        - Capesize:   Length >= 270m, Beam >= 43m
        - Panamax:    Length >= 225m, Beam >= 32m
        - Supramax:   Length >= 190m, Beam >= 30m
        - Handymax:   Length >= 170m, Beam >= 27m  
        - Handysize:  Length >= 140m, Beam >= 20m
        - Small:      Length < 140m
        
        Args:
            length: Vessel length in meters
            width: Vessel beam/width in meters
            
        Returns:
            BulkCarrierClass enum value or None
        """
        if length is None or length <= 0:
            return None
        
        if length >= 270:
            return cls.CAPESIZE
        elif length >= 225:
            # Could be Panamax or large Supramax - use beam to disambiguate
            if width and width >= 38:
                return cls.PANAMAX
            elif width and width < 32:
                return cls.SUPRAMAX
            return cls.PANAMAX
        elif length >= 190:
            return cls.SUPRAMAX
        elif length >= 170:
            return cls.HANDYMAX
        elif length >= 140:
            return cls.HANDYSIZE
        else:
            return cls.SMALL

    @classmethod
    def classify_best(cls, deadweight: Optional[float] = None,
                      length: Optional[float] = None,
                      width: Optional[float] = None) -> Optional['BulkCarrierClass']:
        """
        Classify bulk carrier using best available data.
        Prefers DWT if available, falls back to dimensions.
        
        Args:
            deadweight: Deadweight tonnage (preferred)
            length: Vessel length in meters
            width: Vessel beam in meters
            
        Returns:
            BulkCarrierClass enum value or None
        """
        if deadweight is not None and deadweight > 0:
            return cls.classify(deadweight)
        return cls.classify_by_dimensions(length, width)

    @classmethod
    def from_string(cls, class_str: Optional[str]) -> Optional['BulkCarrierClass']:
        """
        Convert a string to a BulkCarrierClass enum.
        
        Args:
            class_str: Bulk carrier class name as string
            
        Returns:
            BulkCarrierClass enum if valid, None otherwise
        """
        if class_str is None:
            return None
        try:
            return cls(class_str.lower())
        except ValueError:
            return None

    @classmethod
    def large_carriers(cls) -> list['BulkCarrierClass']:
        """Get all large bulk carrier classes (Capesize)."""
        return [cls.CAPESIZE]

    @classmethod
    def medium_carriers(cls) -> list['BulkCarrierClass']:
        """Get all medium bulk carrier classes (Panamax, Supramax)."""
        return [cls.PANAMAX, cls.SUPRAMAX]

    @classmethod
    def small_carriers(cls) -> list['BulkCarrierClass']:
        """Get all small bulk carrier classes (Handymax, Handysize, Small)."""
        return [cls.HANDYMAX, cls.HANDYSIZE, cls.SMALL]


# Display names
_BULK_CLASS_NAMES = {
    BulkCarrierClass.CAPESIZE: "Capesize",
    BulkCarrierClass.PANAMAX: "Panamax",
    BulkCarrierClass.SUPRAMAX: "Supramax",
    BulkCarrierClass.HANDYMAX: "Handymax",
    BulkCarrierClass.HANDYSIZE: "Handysize",
    BulkCarrierClass.SMALL: "Small Bulk",
}

# Detailed descriptions
_BULK_CLASS_DESCRIPTIONS = {
    BulkCarrierClass.CAPESIZE: "Largest bulk carriers, too large for Suez/Panama canals. Primarily carry iron ore and coal on long-haul routes (Brazil/Australia to Asia).",
    BulkCarrierClass.PANAMAX: "Maximum size for old Panama Canal locks. Widely used for coal, grain, and iron ore on diverse routes.",
    BulkCarrierClass.SUPRAMAX: "Versatile mid-size carriers with self-loading/unloading cranes. Popular for grain, sugar, cement, and fertilizer.",
    BulkCarrierClass.HANDYMAX: "Flexible medium-size carriers. Handle grain, steel, and forest products on regional routes.",
    BulkCarrierClass.HANDYSIZE: "Smaller versatile carriers for minor bulk trades. Steel, grain, fertilizer, and general bulk.",
    BulkCarrierClass.SMALL: "Small coastal and regional bulk carriers for aggregates, sand, and minor bulk cargoes.",
}

# DWT ranges for classification (min inclusive, max exclusive)
_BULK_CLASS_RANGES = {
    BulkCarrierClass.CAPESIZE: (100000, float('inf')),
    BulkCarrierClass.PANAMAX: (65000, 100000),
    BulkCarrierClass.SUPRAMAX: (50000, 65000),
    BulkCarrierClass.HANDYMAX: (40000, 50000),
    BulkCarrierClass.HANDYSIZE: (15000, 40000),
    BulkCarrierClass.SMALL: (0, 15000),
}

# Typical cargo for each class
_BULK_CLASS_CARGOES = {
    BulkCarrierClass.CAPESIZE: "Iron ore, Coal (long-haul)",
    BulkCarrierClass.PANAMAX: "Coal, Grain, Iron ore",
    BulkCarrierClass.SUPRAMAX: "Grain, Sugar, Cement, Fertilizer",
    BulkCarrierClass.HANDYMAX: "Grain, Steel, Forest products",
    BulkCarrierClass.HANDYSIZE: "Minor bulk, Steel, Grain, Fertilizer",
    BulkCarrierClass.SMALL: "Coastal bulk, Aggregates",
}

# Map colors for each class
_BULK_CLASS_COLORS = {
    BulkCarrierClass.CAPESIZE: "#8B0000",     # Dark red
    BulkCarrierClass.PANAMAX: "#FF4500",       # Orange-red
    BulkCarrierClass.SUPRAMAX: "#FF8C00",      # Dark orange
    BulkCarrierClass.HANDYMAX: "#DAA520",      # Goldenrod
    BulkCarrierClass.HANDYSIZE: "#BDB76B",     # Dark khaki
    BulkCarrierClass.SMALL: "#808080",         # Gray
}

"""
Service for tracking and classifying bulk carriers (dry bulk) alongside tankers (wet bulk).

Provides:
- Classification of vessels into categories (Tanker, Bulk Carrier, Cargo, Other)
- Sub-classification of bulk carriers (Capesize, Panamax, Supramax, Handymax, Handysize)
- Statistics and logging for vessel classification breakdown
- Name-based heuristics to distinguish bulk carriers from container ships
"""

import logging
from typing import Dict, List, Optional

from models.vessel import Vessel
from enums.ship_type import ShipType
from enums.tanker_class import TankerClass
from enums.bulk_carrier_class import BulkCarrierClass

logger = logging.getLogger(__name__)


# Keywords commonly found in bulk carrier vessel names
BULK_CARRIER_NAME_KEYWORDS = [
    'BULK', 'BULKER', 'ORE', 'MINERAL', 'GRAIN',
    'CAPE', 'CAPESIZE', 'PANAMAX', 'SUPRAMAX', 'HANDYMAX', 'HANDYSIZE',
    'COAL', 'IRON', 'BAUXITE',
]

# Keywords that suggest a vessel is NOT a bulk carrier (container ships, etc.)
NON_BULK_NAME_KEYWORDS = [
    'CONTAINER', 'MAERSK', 'MSC ', 'COSCO', 'EVERGREEN', 'CMA CGM',
    'RORO', 'RO-RO', 'CAR CARRIER', 'VEHICLE',
]

# Destination keywords suggesting bulk cargo
BULK_DESTINATION_KEYWORDS = [
    'ORE', 'COAL', 'GRAIN', 'BULK', 'MINERAL', 'CEMENT', 'FERTILIZER',
    'IRON', 'BAUXITE', 'SUGAR', 'SOYA', 'WHEAT', 'CORN',
]


def looks_like_bulk_carrier(vessel: Vessel) -> bool:
    """
    Heuristic to determine if a cargo-type vessel (AIS 70-79) is likely a bulk carrier.
    
    Since AIS doesn't distinguish between cargo sub-types, we use:
    1. Vessel name keywords (most reliable from AIS data)
    2. Destination keywords (suggests bulk commodity trade)
    3. Dimension-based heuristics (bulk carriers have lower L/B ratio than container ships)
    4. Default: large cargo vessels are more likely bulk carriers
    
    Args:
        vessel: Vessel object with ship_type in range 70-79
        
    Returns:
        True if the vessel is likely a bulk carrier
    """
    # Check vessel name for non-bulk keywords first (container ships, etc.)
    if vessel.name and vessel.name.upper() != "UNKNOWN":
        name_upper = vessel.name.upper()
        for keyword in NON_BULK_NAME_KEYWORDS:
            if keyword in name_upper:
                return False
    
    # Check vessel name for bulk carrier keywords
    if vessel.name and vessel.name.upper() != "UNKNOWN":
        name_upper = vessel.name.upper()
        for keyword in BULK_CARRIER_NAME_KEYWORDS:
            if keyword in name_upper:
                return True
    
    # Check destination for bulk-related ports/terminals
    if vessel.destination:
        dest_upper = vessel.destination.upper()
        for keyword in BULK_DESTINATION_KEYWORDS:
            if keyword in dest_upper:
                return True
    
    # For large cargo vessels, use length-to-beam ratio heuristic
    # Bulk carriers typically have L/B ratio of 5.5-6.5
    # Container ships typically have L/B ratio of 6.5-8.0+
    if vessel.length and vessel.length > 150:
        if vessel.width and vessel.width > 0:
            ratio = vessel.length / vessel.width
            if ratio < 7.0:
                return True
            else:
                return False  # Likely a container ship
    
    # Default: for large cargo vessels (>100m), treat as potential bulk carrier
    # Bulk carriers outnumber container ships globally
    if vessel.length and vessel.length > 100:
        return True
    
    return False


def classify_vessel(vessel: Vessel) -> None:
    """
    Classify a vessel into category and sub-class.
    Modifies the vessel in-place by setting vessel_category and bulk_carrier_class.
    
    Args:
        vessel: Vessel to classify
    """
    if vessel.ship_type is None:
        vessel.vessel_category = "Unknown"
        return
    
    ship_type_val = vessel.ship_type.value if isinstance(vessel.ship_type, ShipType) else int(vessel.ship_type)
    
    # Tanker classification (80-89)
    if 80 <= ship_type_val <= 89:
        vessel.vessel_category = "Tanker"
        # Tanker class from DWT or dimensions
        if vessel.deadweight:
            vessel.tanker_class = TankerClass.classify(vessel.deadweight)
        elif vessel.length:
            # Rough length-based estimate for tanker class
            vessel.tanker_class = _estimate_tanker_class_from_length(vessel.length)
        return
    
    # Cargo/Bulk classification (70-79)
    if 70 <= ship_type_val <= 79:
        if looks_like_bulk_carrier(vessel):
            vessel.vessel_category = "Bulk Carrier"
            vessel.is_bulk_carrier = True
            # Classify by size
            vessel.bulk_carrier_class = BulkCarrierClass.classify_best(
                deadweight=vessel.deadweight,
                length=vessel.length,
                width=vessel.width
            )
        else:
            vessel.vessel_category = "Cargo"
        return
    
    vessel.vessel_category = "Other"


def classify_all_vessels(vessels: Dict[int, Vessel]) -> Dict[str, any]:
    """
    Classify all vessels and return statistics.
    
    Args:
        vessels: Dictionary of MMSI -> Vessel objects
        
    Returns:
        Dictionary with classification statistics
    """
    stats = {
        'total': len(vessels),
        'tankers': 0,
        'bulk_carriers': 0,
        'cargo_other': 0,
        'other': 0,
        'tanker_classes': {},
        'bulk_classes': {},
    }
    
    for vessel in vessels.values():
        classify_vessel(vessel)
        
        if vessel.vessel_category == "Tanker":
            stats['tankers'] += 1
            if vessel.tanker_class:
                cls_name = vessel.tanker_class.display_name
                stats['tanker_classes'][cls_name] = stats['tanker_classes'].get(cls_name, 0) + 1
                
        elif vessel.vessel_category == "Bulk Carrier":
            stats['bulk_carriers'] += 1
            if vessel.bulk_carrier_class:
                cls_name = vessel.bulk_carrier_class.display_name
                stats['bulk_classes'][cls_name] = stats['bulk_classes'].get(cls_name, 0) + 1
                
        elif vessel.vessel_category == "Cargo":
            stats['cargo_other'] += 1
        else:
            stats['other'] += 1
    
    return stats


def log_classification_stats(stats: Dict) -> None:
    """Print classification statistics to console and logger."""
    msg_lines = [
        f"\n📊 VESSEL CLASSIFICATION STATISTICS:",
        f"   Total vessels tracked: {stats['total']}",
        f"   🛢️  Tankers (wet bulk): {stats['tankers']}",
    ]
    
    if stats['tanker_classes']:
        for cls_name, count in sorted(stats['tanker_classes'].items(), key=lambda x: -x[1]):
            msg_lines.append(f"      • {cls_name}: {count}")
    
    msg_lines.append(f"   📦 Bulk Carriers (dry bulk): {stats['bulk_carriers']}")
    
    if stats['bulk_classes']:
        for cls_name, count in sorted(stats['bulk_classes'].items(), key=lambda x: -x[1]):
            msg_lines.append(f"      • {cls_name}: {count}")
    
    msg_lines.append(f"   🚢 Other Cargo: {stats['cargo_other']}")
    msg_lines.append(f"   ❓ Other Types: {stats['other']}")
    
    full_msg = "\n".join(msg_lines)
    logger.info(full_msg)
    print(full_msg)


def get_bulk_carriers(vessels: Dict[int, Vessel]) -> Dict[int, Vessel]:
    """Get only bulk carrier vessels from the vessel dictionary."""
    return {
        mmsi: v for mmsi, v in vessels.items()
        if getattr(v, 'is_bulk_carrier', False)
    }


def get_bulk_carriers_by_class(vessels: Dict[int, Vessel], 
                                bulk_class: BulkCarrierClass) -> Dict[int, Vessel]:
    """Get bulk carriers filtered by size class."""
    return {
        mmsi: v for mmsi, v in vessels.items()
        if getattr(v, 'is_bulk_carrier', False) 
        and getattr(v, 'bulk_carrier_class', None) == bulk_class
    }


def get_tankers(vessels: Dict[int, Vessel]) -> Dict[int, Vessel]:
    """Get only tanker vessels from the vessel dictionary."""
    return {
        mmsi: v for mmsi, v in vessels.items()
        if getattr(v, 'vessel_category', None) == "Tanker"
    }


def _estimate_tanker_class_from_length(length: float) -> Optional[TankerClass]:
    """
    Rough tanker class estimate based on vessel length.
    
    Typical lengths:
    - ULCC/VLCC: 330m+
    - Suezmax: 270-330m
    - Aframax: 230-270m
    - Panamax: 200-230m
    - Handymax: 170-200m
    - Handysize: 120-170m
    - Small: <120m
    """
    if length >= 330:
        return TankerClass.VLCC  # Could be ULCC too
    elif length >= 270:
        return TankerClass.SUEZMAX
    elif length >= 230:
        return TankerClass.AFRAMAX
    elif length >= 200:
        return TankerClass.PANAMAX
    elif length >= 170:
        return TankerClass.HANDYMAX
    elif length >= 120:
        return TankerClass.HANDYSIZE
    else:
        return TankerClass.SMALL

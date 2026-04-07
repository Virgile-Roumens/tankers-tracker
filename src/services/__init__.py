"""
Services package for Tankers Tracker.

Provides high-level business logic and service layers.
"""

from .region_manager import RegionManager
from .vessel_display_service import VesselDisplayService
from .vessel_lookup import lookup_vessel_in_tracker, lookup_vessel_via_websocket
from .bulk_tracking_service import (
    classify_vessel,
    classify_all_vessels,
    log_classification_stats,
    looks_like_bulk_carrier,
    get_bulk_carriers,
    get_bulk_carriers_by_class,
    get_tankers,
)

__all__ = [
    'RegionManager',
    'VesselDisplayService',
    'lookup_vessel_in_tracker',
    'lookup_vessel_via_websocket',
    'classify_vessel',
    'classify_all_vessels',
    'log_classification_stats',
    'looks_like_bulk_carrier',
    'get_bulk_carriers',
    'get_bulk_carriers_by_class',
    'get_tankers',
]

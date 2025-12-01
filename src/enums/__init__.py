"""
Enums package for Tankers Tracker.

This package contains enum classes for type-safe constants used throughout the application.
"""

from .ship_type import ShipType
from .navigational_status import NavigationalStatus
from .region import Region
from .tanker_class import TankerClass

__all__ = ['ShipType', 'NavigationalStatus', 'Region', 'TankerClass']


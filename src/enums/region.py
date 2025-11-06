"""
Region Enum for geographic regions and strategic shipping lanes.

This module defines the Region enum which provides type-safe region definitions
to prevent typos and inconsistencies in region handling throughout the application.
"""

from enum import Enum
from typing import Optional, List, Dict


class Region(str, Enum):
    """
    Strategic tanker tracking regions and shipping lanes.
    
    Organizes all major oil shipping routes and chokepoints into
    type-safe region definitions.
    """
    
    # MIDDLE EAST - Major oil export regions
    PERSIAN_GULF = "persian_gulf"
    STRAIT_HORMUZ = "strait_hormuz"
    RED_SEA = "red_sea"
    BAB_EL_MANDEB = "bab_el_mandeb"
    
    # SUEZ & MEDITERRANEAN - Europe/Asia route
    SUEZ_CANAL = "suez_canal"
    SUEZ_NORTH = "suez_north"
    SUEZ_SOUTH = "suez_south"
    MEDITERRANEAN_EAST = "mediterranean_east"
    MEDITERRANEAN_WEST = "mediterranean_west"
    GIBRALTAR = "gibraltar"
    
    # SOUTHEAST ASIA - Critical shipping lanes
    MALACCA_STRAIT = "malacca_strait"
    SINGAPORE_STRAIT = "singapore_strait"
    SUNDA_STRAIT = "sunda_strait"
    SOUTH_CHINA_SEA = "south_china_sea"
    
    # AMERICAS - Major import/export regions
    US_GULF = "us_gulf"
    CARIBBEAN = "caribbean"
    PANAMA_CANAL = "panama_canal"
    VENEZUELA_COAST = "venezuela_coast"
    BRAZIL_COAST = "brazil_coast"
    
    # EUROPE & NORTH SEA - Major consumption region
    NORTH_SEA = "north_sea"
    ENGLISH_CHANNEL = "english_channel"
    BALTIC_SEA = "baltic_sea"
    NORWEGIAN_SEA = "norwegian_sea"
    
    # AFRICA - Emerging routes
    WEST_AFRICA = "west_africa"
    CAPE_GOOD_HOPE = "cape_good_hope"
    EAST_AFRICA = "east_africa"
    
    # ASIA-PACIFIC - Major consumers
    JAPAN_COAST = "japan_coast"
    KOREA_STRAIT = "korea_strait"
    TAIWAN_STRAIT = "taiwan_strait"
    EAST_CHINA_SEA = "east_china_sea"
    
    @property
    def emoji(self) -> str:
        """
        Get emoji for this region.
        
        Returns:
            str: Emoji character for the region
        """
        return _REGION_EMOJIS.get(self, "📍")
    
    @property
    def display_name(self) -> str:
        """
        Get human-readable display name for this region.
        
        Returns:
            str: Formatted region name
        """
        return _REGION_NAMES.get(self, self.value.replace('_', ' ').title())
    
    @property
    def display_name_with_emoji(self) -> str:
        """
        Get display name with emoji prefix.
        
        Returns:
            str: Emoji + display name
        """
        return f"{self.emoji} {self.display_name}"
    
    @property
    def category(self) -> str:
        """
        Get the geographic category this region belongs to.
        
        Returns:
            str: Category name (e.g., "MIDDLE EAST", "SUEZ & MEDITERRANEAN")
        """
        return _REGION_CATEGORIES.get(self, "OTHER")
    
    @classmethod
    def from_string(cls, region_str: Optional[str]) -> Optional['Region']:
        """
        Convert a string to a Region enum.
        
        Args:
            region_str: Region name as string
            
        Returns:
            Region enum if valid, None otherwise
        """
        if region_str is None:
            return None
        
        # Try direct lookup
        try:
            return cls(region_str)
        except ValueError:
            # Try case-insensitive lookup
            for region in cls:
                if region.value.lower() == region_str.lower():
                    return region
            return None
    
    @classmethod
    def by_category(cls, category: str) -> List['Region']:
        """
        Get all regions in a specific category.
        
        Args:
            category: Category name
            
        Returns:
            List of Region enums in that category
        """
        return [region for region in cls if region.category == category]
    
    @classmethod
    def all_chokepoints(cls) -> List['Region']:
        """
        Get all critical chokepoints for tanker shipping.
        
        Returns:
            List of critical chokepoint regions
        """
        chokepoints = {
            cls.STRAIT_HORMUZ,      # 20% of global oil
            cls.MALACCA_STRAIT,     # 25% of global oil
            cls.SUEZ_CANAL,         # Europe-Asia shortcut
            cls.PANAMA_CANAL,       # Atlantic-Pacific shortcut
            cls.BAB_EL_MANDEB,      # Red Sea-Indian Ocean gateway
        }
        return list(chokepoints)


# Emoji mappings for regions - using universal symbols that work everywhere
_REGION_EMOJIS = {
    # Middle East - Oil regions
    Region.PERSIAN_GULF: "🛢️",
    Region.STRAIT_HORMUZ: "⚠️",
    Region.RED_SEA: "🌊",
    Region.BAB_EL_MANDEB: "⚠️",
    
    # Suez & Mediterranean
    Region.SUEZ_CANAL: "📍",
    Region.SUEZ_NORTH: "📍",
    Region.SUEZ_SOUTH: "📍",
    Region.MEDITERRANEAN_EAST: "💧",
    Region.MEDITERRANEAN_WEST: "💧",
    Region.GIBRALTAR: "📍",
    
    # Southeast Asia
    Region.MALACCA_STRAIT: "⚠️",
    Region.SINGAPORE_STRAIT: "📍",
    Region.SUNDA_STRAIT: "💧",
    Region.SOUTH_CHINA_SEA: "💧",
    
    # Americas
    Region.US_GULF: "🛢️",
    Region.CARIBBEAN: "🏝️",
    Region.PANAMA_CANAL: "📍",
    Region.VENEZUELA_COAST: "🛢️",
    Region.BRAZIL_COAST: "🛢️",
    
    # Europe & North Sea
    Region.NORTH_SEA: "💧",
    Region.ENGLISH_CHANNEL: "📍",
    Region.BALTIC_SEA: "❄️",
    Region.NORWEGIAN_SEA: "💧",
    
    # Africa
    Region.WEST_AFRICA: "🛢️",
    Region.CAPE_GOOD_HOPE: "🌊",
    Region.EAST_AFRICA: "🌊",
    
    # Asia-Pacific
    Region.JAPAN_COAST: "💧",
    Region.KOREA_STRAIT: "💧",
    Region.TAIWAN_STRAIT: "💧",
    Region.EAST_CHINA_SEA: "💧",
}

# Human-readable display names for regions
_REGION_NAMES = {
    Region.PERSIAN_GULF: "Persian Gulf",
    Region.STRAIT_HORMUZ: "Strait of Hormuz",
    Region.RED_SEA: "Red Sea",
    Region.BAB_EL_MANDEB: "Bab el-Mandeb",
    
    Region.SUEZ_CANAL: "Suez Canal",
    Region.SUEZ_NORTH: "Suez North (Port Said)",
    Region.SUEZ_SOUTH: "Suez South (Gulf of Suez)",
    Region.MEDITERRANEAN_EAST: "East Mediterranean",
    Region.MEDITERRANEAN_WEST: "West Mediterranean",
    Region.GIBRALTAR: "Strait of Gibraltar",
    
    Region.MALACCA_STRAIT: "Strait of Malacca",
    Region.SINGAPORE_STRAIT: "Singapore Strait",
    Region.SUNDA_STRAIT: "Sunda Strait",
    Region.SOUTH_CHINA_SEA: "South China Sea",
    
    Region.US_GULF: "US Gulf Coast",
    Region.CARIBBEAN: "Caribbean",
    Region.PANAMA_CANAL: "Panama Canal",
    Region.VENEZUELA_COAST: "Venezuelan Coast",
    Region.BRAZIL_COAST: "Brazilian Coast",
    
    Region.NORTH_SEA: "North Sea",
    Region.ENGLISH_CHANNEL: "English Channel",
    Region.BALTIC_SEA: "Baltic Sea",
    Region.NORWEGIAN_SEA: "Norwegian Sea",
    
    Region.WEST_AFRICA: "West Africa",
    Region.CAPE_GOOD_HOPE: "Cape of Good Hope",
    Region.EAST_AFRICA: "East Africa",
    
    Region.JAPAN_COAST: "Japan Coast",
    Region.KOREA_STRAIT: "Korea Strait",
    Region.TAIWAN_STRAIT: "Taiwan Strait",
    Region.EAST_CHINA_SEA: "East China Sea",
}

# Region category classifications
_REGION_CATEGORIES = {
    Region.PERSIAN_GULF: "MIDDLE EAST",
    Region.STRAIT_HORMUZ: "MIDDLE EAST",
    Region.RED_SEA: "MIDDLE EAST",
    Region.BAB_EL_MANDEB: "MIDDLE EAST",
    
    Region.SUEZ_CANAL: "SUEZ & MEDITERRANEAN",
    Region.SUEZ_NORTH: "SUEZ & MEDITERRANEAN",
    Region.SUEZ_SOUTH: "SUEZ & MEDITERRANEAN",
    Region.MEDITERRANEAN_EAST: "SUEZ & MEDITERRANEAN",
    Region.MEDITERRANEAN_WEST: "SUEZ & MEDITERRANEAN",
    Region.GIBRALTAR: "SUEZ & MEDITERRANEAN",
    
    Region.MALACCA_STRAIT: "SOUTHEAST ASIA",
    Region.SINGAPORE_STRAIT: "SOUTHEAST ASIA",
    Region.SUNDA_STRAIT: "SOUTHEAST ASIA",
    Region.SOUTH_CHINA_SEA: "SOUTHEAST ASIA",
    
    Region.US_GULF: "AMERICAS",
    Region.CARIBBEAN: "AMERICAS",
    Region.PANAMA_CANAL: "AMERICAS",
    Region.VENEZUELA_COAST: "AMERICAS",
    Region.BRAZIL_COAST: "AMERICAS",
    
    Region.NORTH_SEA: "EUROPE",
    Region.ENGLISH_CHANNEL: "EUROPE",
    Region.BALTIC_SEA: "EUROPE",
    Region.NORWEGIAN_SEA: "EUROPE",
    
    Region.WEST_AFRICA: "AFRICA",
    Region.CAPE_GOOD_HOPE: "AFRICA",
    Region.EAST_AFRICA: "AFRICA",
    
    Region.JAPAN_COAST: "ASIA-PACIFIC",
    Region.KOREA_STRAIT: "ASIA-PACIFIC",
    Region.TAIWAN_STRAIT: "ASIA-PACIFIC",
    Region.EAST_CHINA_SEA: "ASIA-PACIFIC",
}



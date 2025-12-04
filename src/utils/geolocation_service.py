"""
Geolocation service for mapping coordinates to geographic regions and countries.
Uses free public APIs to identify if coordinates are in international waters or territorial waters.
"""

import asyncio
import logging
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)

# Optional async support (only imported if needed)
try:
    import aiohttp
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False
    logger.debug("aiohttp not available - async geolocation disabled")


class GeolocationService:
    """Service for determining geographic location and water classification."""
    
    # Cache for coordinates to avoid repeated API calls
    _cache: Dict[Tuple[float, float], Dict] = {}
    
    @staticmethod
    def _are_coordinates_close(lat1: float, lon1: float, lat2: float, lon2: float, threshold: float = 0.1) -> bool:
        """Check if two coordinates are within threshold degrees of each other."""
        return abs(lat1 - lat2) <= threshold and abs(lon1 - lon2) <= threshold
    
    @classmethod
    def _get_cached_location(cls, lat: float, lon: float) -> Optional[Dict]:
        """Check if a similar coordinate is in cache."""
        for (cached_lat, cached_lon), result in cls._cache.items():
            if cls._are_coordinates_close(lat, lon, cached_lat, cached_lon):
                return result
        return None
    
    @classmethod
    async def identify_location_async(cls, lat: float, lon: float) -> Dict:
        """
        Identify if coordinates are in international waters or territorial waters.
        
        Uses the Nominatim API (OpenStreetMap) for reverse geocoding.
        Requires aiohttp to be installed.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dict with 'country', 'water_type', 'location' information
        """
        if not ASYNC_AVAILABLE:
            logger.warning("aiohttp not installed - using sync mode instead")
            return cls.identify_location_sync(lat, lon)
        
        # Check cache first
        cached = cls._get_cached_location(lat, lon)
        if cached:
            return cached
        
        try:
            async with aiohttp.ClientSession() as session:
                # Try Nominatim API (OpenStreetMap's free reverse geocoding)
                url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
                headers = {"User-Agent": "tankers-tracker"}
                
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = cls._parse_nominatim_response(data, lat, lon)
                    else:
                        result = cls._default_location(lat, lon)
            
            # Cache the result
            cls._cache[(lat, lon)] = result
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"Geolocation timeout for {lat}, {lon}")
            return cls._default_location(lat, lon)
        except Exception as e:
            logger.error(f"Geolocation error: {e}")
            return cls._default_location(lat, lon)
    
    @staticmethod
    def _parse_nominatim_response(data: Dict, lat: float, lon: float) -> Dict:
        """Parse Nominatim API response."""
        address = data.get("address", {})
        country = address.get("country", "Unknown")
        
        # Determine water type based on response
        if "ocean" in data.get("name", "").lower():
            water_type = "international_waters"
        elif address.get("country"):
            water_type = "territorial_waters"
        else:
            water_type = "unknown"
        
        return {
            "country": country,
            "water_type": water_type,
            "location": data.get("name", "Unknown"),
            "lat": lat,
            "lon": lon
        }
    
    @staticmethod
    def _default_location(lat: float, lon: float) -> Dict:
        """Return default location when API fails."""
        return {
            "country": "Unknown",
            "water_type": "unknown",
            "location": f"({lat:.2f}, {lon:.2f})",
            "lat": lat,
            "lon": lon
        }
    
    @classmethod
    def identify_location_sync(cls, lat: float, lon: float) -> Dict:
        """Synchronous version using simple geographic logic (no API call)."""
        # Basic checks for major geographic regions
        result = cls._default_location(lat, lon)
        
        # Check if in EEZ (Exclusive Economic Zone) - simplified logic
        # International waters are typically beyond 200nm from shore
        # For this simplified version, we'll use known geographic zones
        
        if cls._is_in_known_territorial_waters(lat, lon):
            result["water_type"] = "territorial_waters"
            result["country"] = cls._get_country_by_region(lat, lon)
        else:
            result["water_type"] = "international_waters"
        
        return result
    
    @staticmethod
    def _is_in_known_territorial_waters(lat: float, lon: float) -> bool:
        """Check if coordinates are in known territorial water zones."""
        # Simplified version - in production, you'd use proper EEZ data
        territorial_zones = [
            # (lat_min, lat_max, lon_min, lon_max)
            (23, 31, 47, 61, "Persian Gulf"),
            (24, 27, 54, 58, "Strait of Hormuz"),
            (30.5, 33, 32, 35, "Mediterranean/Suez"),
            (0.5, 6, 98, 105, "Malacca Strait"),
            (5, 25, 105, 120, "South China Sea"),
            (25, 31, -98, -80, "US Gulf"),
            (49, 62, -6, 10, "North Sea"),
        ]
        
        for lat_min, lat_max, lon_min, lon_max, _ in territorial_zones:
            if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                return True
        
        return False
    
    @staticmethod
    def _get_country_by_region(lat: float, lon: float) -> str:
        """Get country name based on region."""
        # Simplified mapping
        region_map = {
            (23, 31, 47, 61): "Saudi Arabia/UAE/Iran/Iraq",
            (24, 27, 54, 58): "UAE/Iran",
            (30.5, 33, 32, 35): "Egypt",
            (0.5, 6, 98, 105): "Malaysia/Indonesia/Singapore",
            (5, 25, 105, 120): "China/Vietnam/Philippines",
            (25, 31, -98, -80): "USA",
            (49, 62, -6, 10): "UK/Netherlands/Norway",
        }
        
        for (lat_min, lat_max, lon_min, lon_max), country in region_map.items():
            if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                return country
        
        return "Unknown"


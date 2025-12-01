"""
Enhanced map integration module that adds new features to existing map generation.
Works alongside the existing search functionality to provide:
- Directional arrow markers
- Geolocation water classification
- Enhanced vessel search capabilities
"""

import logging
from typing import Dict, Optional, List
import folium
from models.vessel import Vessel
from utils.geolocation_service import GeolocationService
from utils.vessel_marker_service import VesselMarkerService
from utils.vessel_search_service import VesselSearchService
from config import VESSEL_MARKER_RADIUS

logger = logging.getLogger(__name__)


class EnhancedMapIntegration:
    """
    Integration layer for new features into existing map generation.
    Enhances vessel markers with directional arrows and geolocation info.
    """
    
    def __init__(self):
        """Initialize the integration layer."""
        self.geo_service = GeolocationService()
        self.marker_service = VesselMarkerService()
        self.search_service = None  # Will be initialized when vessels are provided
    
    def update_vessels(self, vessels_dict: Dict[int, Vessel]):
        """Update the vessel search service with current vessels."""
        self.search_service = VesselSearchService(vessels_dict)
    
    def enhance_vessel_popup(self, vessel: Vessel, existing_popup_html: str) -> str:
        """
        Enhance existing popup with geolocation and water type information.
        
        Args:
            vessel: Vessel object
            existing_popup_html: Existing popup HTML from map_generator
            
        Returns:
            Enhanced popup HTML with geolocation info
        """
        if not vessel.has_position():
            return existing_popup_html
        
        try:
            # Get location information
            location = self.geo_service.identify_location_sync(
                vessel.lat, vessel.lon
            )
            
            # Insert geolocation info into popup
            location_html = f"""
                <tr style="background-color: #f0f0f0;">
                    <td colspan="2" style="padding-top: 8px; border-top: 1px solid #ddd;"><b>🌍 Location</b></td>
                </tr>
                <tr>
                    <td><b>Region:</b></td>
                    <td>{location.get('location', 'Unknown')}</td>
                </tr>
                <tr>
                    <td><b>Waters:</b></td>
                    <td>{location.get('water_type', 'Unknown').replace('_', ' ').title()}</td>
                </tr>
                <tr>
                    <td><b>Country:</b></td>
                    <td>{location.get('country', 'Unknown')}</td>
                </tr>
            """
            
            # Insert before closing table tag
            enhanced_html = existing_popup_html.replace(
                "</table>",
                location_html + "</table>"
            )
            
            return enhanced_html
            
        except Exception as e:
            logger.warning(f"Error enhancing popup for vessel {vessel.mmsi}: {e}")
            return existing_popup_html
    
    def get_directional_icon_svg(self, vessel: Vessel) -> Optional[str]:
        """
        Get SVG arrow icon for vessel if it has heading information.
        
        Args:
            vessel: Vessel object
            
        Returns:
            SVG string or None
        """
        try:
            if not vessel.course and not vessel.heading:
                return None
            
            # Use heading if available, otherwise course
            heading = vessel.heading if vessel.heading is not None else int(vessel.course or 0)
            
            # Only show arrows for moving vessels
            if vessel.speed and vessel.speed > 0.5:
                color = vessel.ship_type.get_color() if vessel.ship_type else '#808080'
                svg = self.marker_service.get_arrow_icon(
                    heading=heading,
                    color=color,
                    size=6
                )
                return svg
            
            return None
            
        except Exception as e:
            logger.debug(f"Error generating icon for vessel {vessel.mmsi}: {e}")
            return None
    
    def get_marker_icon_html(self, vessel: Vessel) -> str:
        """
        Get complete HTML icon string for use in markers.
        Falls back to empty string if SVG generation fails.
        
        Args:
            vessel: Vessel object
            
        Returns:
            HTML icon string or empty string
        """
        try:
            svg = self.get_directional_icon_svg(vessel)
            if svg:
                return self.marker_service.get_icon_html_uri(svg)
            return ""
        except Exception as e:
            logger.debug(f"Error getting icon HTML: {e}")
            return ""
    
    def analyze_unknown_vessels(self) -> Dict:
        """
        Analyze vessels with unknown ship types.
        
        Returns:
            Dict with analysis results
        """
        if not self.search_service:
            return {'error': 'No vessels loaded'}
        
        try:
            unknown = self.search_service.get_unknown_vessels()
            
            analysis = {
                'total_unknown': len(unknown),
                'vessels': []
            }
            
            for vessel in unknown:
                if vessel.has_position():
                    location = self.geo_service.identify_location_sync(
                        vessel.lat, vessel.lon
                    )
                else:
                    location = {'country': 'N/A', 'water_type': 'N/A'}
                
                analysis['vessels'].append({
                    'mmsi': vessel.mmsi,
                    'name': vessel.name or 'Unknown',
                    'imo': vessel.imo,
                    'callsign': vessel.callsign,
                    'destination': vessel.destination,
                    'location': location.get('location', 'Unknown'),
                    'water_type': location.get('water_type', 'Unknown'),
                    'speed': vessel.speed,
                    'course': vessel.course
                })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing unknown vessels: {e}")
            return {'error': str(e)}
    
    def get_vessel_statistics(self) -> Dict:
        """
        Get comprehensive statistics about vessels.
        
        Returns:
            Dict with vessel statistics
        """
        if not self.search_service:
            return {'error': 'No vessels loaded'}
        
        try:
            stats = {
                'total_vessels': len(self.search_service.vessels_dict),
                'stationary': len(self.search_service.get_stationary_vessels()),
                'moving': len(self.search_service.get_fast_moving_vessels(5.0)),
                'unknown_types': len(self.search_service.get_unknown_vessels()),
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {'error': str(e)}
    
    def search_vessel(self, query: str, search_type: str = 'name') -> List[Vessel]:
        """
        Search for vessels using various criteria.
        
        Args:
            query: Search query string
            search_type: Type of search ('name', 'mmsi', 'destination', 'callsign', 'imo')
            
        Returns:
            List of matching Vessel objects
        """
        if not self.search_service:
            return []
        
        try:
            if search_type == 'name':
                return self.search_service.search_by_name(query, partial=True)
            elif search_type == 'mmsi':
                vessel = self.search_service.search_by_mmsi(int(query))
                return [vessel] if vessel else []
            elif search_type == 'destination':
                return self.search_service.search_by_destination(query, partial=True)
            elif search_type == 'callsign':
                vessel = self.search_service.search_by_callsign(query)
                return [vessel] if vessel else []
            elif search_type == 'imo':
                vessel = self.search_service.search_by_imo(int(query))
                return [vessel] if vessel else []
            else:
                return []
        except ValueError:
            logger.warning(f"Invalid search query: {query} for type {search_type}")
            return []
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def get_location_info(self, vessel: Vessel) -> Dict:
        """
        Get detailed location information for a vessel.
        
        Args:
            vessel: Vessel object
            
        Returns:
            Dict with location information
        """
        if not vessel.has_position():
            return {'error': 'Vessel has no position'}
        
        try:
            return self.geo_service.identify_location_sync(
                vessel.lat, vessel.lon
            )
        except Exception as e:
            logger.error(f"Error getting location: {e}")
            return {'error': str(e)}


"""
Service for creating directional vessel markers with arrows.
"""

import logging
import base64
from typing import Optional

logger = logging.getLogger(__name__)


class VesselMarkerService:
    """Service for creating vessel markers with directional indicators."""
    
    @staticmethod
    def get_arrow_icon(heading: Optional[int], color: str = '#d32f2f', size: int = 24) -> str:
        """
        Generate an SVG arrow icon pointing in the direction of heading.
        
        Args:
            heading: Heading in degrees (0-359), where 0 is North. None for stationary vessel.
            color: Hex color for the arrow
            size: Size of the icon in pixels
            
        Returns:
            SVG string for the arrow
        """
        if heading is None:
            return VesselMarkerService.get_circular_icon(color, size)
        
        # Normalize heading to 0-359
        heading = int(heading) % 360
        
        # Rotate arrow to match heading
        # SVG starts with up-pointing arrow (270 degrees in SVG = 0 in navigation)
        svg_rotation = heading - 90
        
        svg = f'''<svg width="{size}" height="{size}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <g transform="rotate({svg_rotation} 12 12)">
        <!-- Arrow body -->
        <polygon points="12,3 20,18 12,15 4,18" fill="{color}" stroke="white" stroke-width="0.5"/>
        <!-- Center circle for stability -->
        <circle cx="12" cy="12" r="2" fill="white" stroke="{color}" stroke-width="0.5"/>
    </g>
</svg>'''
        return svg
    
    @staticmethod
    def get_circular_icon(color: str = '#d32f2f', size: int = 8) -> str:
        """
        Generate a circular icon (fallback for vessels without heading/stationary).
        
        Args:
            color: Hex color for the circle
            size: Size of the icon
            
        Returns:
            SVG string for the circle
        """
        svg = f'''<svg width="{size}" height="{size}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <circle cx="12" cy="12" r="10" fill="{color}" stroke="white" stroke-width="1"/>
</svg>'''
        return svg
    
    @staticmethod
    def get_icon_html_uri(svg_string: str) -> str:
        """
        Convert SVG to data URI for use in HTML/Leaflet.
        
        Args:
            svg_string: SVG content
            
        Returns:
            Data URI string
        """
        svg_bytes = svg_string.encode('utf-8')
        svg_base64 = base64.b64encode(svg_bytes).decode('utf-8')
        return f"data:image/svg+xml;base64,{svg_base64}"
    
    @staticmethod
    def calculate_heading_from_course(course: Optional[float]) -> Optional[int]:
        """
        Convert course over ground to heading.
        
        Args:
            course: Course over ground (0-359)
            
        Returns:
            Heading in degrees, or None if course is None
        """
        return int(course) % 360 if course is not None else None
    
    @staticmethod
    def get_mini_arrow_icon(heading: Optional[int], color: str = '#d32f2f') -> str:
        """
        Get a small arrow icon (3-6px sized).
        
        Args:
            heading: Heading in degrees
            color: Hex color
            
        Returns:
            SVG string
        """
        return VesselMarkerService.get_arrow_icon(heading, color, size=6)


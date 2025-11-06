"""
Enhanced Vessel Display Service

Provides rich vessel information formatting and enhanced popup generation
with special focus on tanker-specific details.
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime

from models.vessel import Vessel
from config import TANKER_TYPES, SHIP_TYPE_NAMES

logger = logging.getLogger(__name__)


class VesselDisplayService:
    """
    Service for generating rich vessel information displays.
    
    Provides formatted popups, tooltips, and detailed vessel cards
    with special attention to tanker-specific information.
    """
    
    # Tanker size classifications
    TANKER_CLASSES = {
        'ULCC': (320000, float('inf')),      # Ultra Large Crude Carrier
        'VLCC': (200000, 320000),            # Very Large Crude Carrier
        'Suezmax': (120000, 200000),         # Suez Canal max size
        'Aframax': (80000, 120000),          # Average Freight Rate Assessment
        'Panamax': (60000, 80000),           # Panama Canal max size
        'Handymax': (40000, 60000),          # Handy maximum
        'Handysize': (10000, 40000),         # Handy size
        'Small': (0, 10000)                  # Small tanker
    }
    
    # Navigation status with colors
    NAV_STATUS_COLORS = {
        0: ('#4CAF50', 'Under way using engine'),
        1: ('#FF9800', 'At anchor'),
        2: ('#F44336', 'Not under command'),
        3: ('#F44336', 'Restricted manoeuvrability'),
        4: ('#FF5722', 'Constrained by draught'),
        5: ('#2196F3', 'Moored'),
        6: ('#F44336', 'Aground'),
        7: ('#00BCD4', 'Engaged in fishing'),
        8: ('#4CAF50', 'Under way sailing'),
        15: ('#9E9E9E', 'Not defined')
    }
    
    def get_vessel_icon(self, vessel: Vessel) -> str:
        """Get appropriate icon for vessel type."""
        if vessel.is_tanker(TANKER_TYPES):
            return '🛢️'
        elif vessel.ship_type in range(70, 80):
            return '📦'
        else:
            return '🚢'
    
    def get_tanker_class(self, vessel: Vessel) -> Optional[str]:
        """
        Determine tanker size classification.
        
        Args:
            vessel: Vessel object
            
        Returns:
            Tanker class name or None
        """
        if not vessel.is_tanker(TANKER_TYPES) or not vessel.deadweight:
            return None
        
        dwt = vessel.deadweight
        for class_name, (min_dwt, max_dwt) in self.TANKER_CLASSES.items():
            if min_dwt <= dwt < max_dwt:
                return class_name
        
        return 'Unknown'
    
    def estimate_cargo_capacity(self, vessel: Vessel) -> Optional[str]:
        """
        Estimate cargo capacity based on vessel dimensions and type.
        
        Args:
            vessel: Vessel object
            
        Returns:
            Formatted capacity string
        """
        if vessel.deadweight:
            dwt = vessel.deadweight
            if dwt >= 1000000:
                return f"{dwt/1000000:.1f}M tonnes DWT"
            elif dwt >= 1000:
                return f"{dwt/1000:.0f}K tonnes DWT"
            else:
                return f"{dwt:.0f} tonnes DWT"
        
        if vessel.gross_tonnage:
            gt = vessel.gross_tonnage
            if gt >= 1000:
                return f"{gt/1000:.0f}K GT"
            else:
                return f"{gt:.0f} GT"
        
        # Estimate from dimensions
        if vessel.length and vessel.width and vessel.draught:
            volume = vessel.length * vessel.width * vessel.draught * 0.7  # cargo factor
            if vessel.is_tanker(TANKER_TYPES):
                # Crude oil: ~0.85 tonnes/m³
                capacity = volume * 0.85
            else:
                # General cargo: ~0.5 tonnes/m³
                capacity = volume * 0.5
            
            if capacity >= 1000:
                return f"~{capacity/1000:.0f}K tonnes (est.)"
            else:
                return f"~{capacity:.0f} tonnes (est.)"
        
        return None
    
    def format_speed_info(self, vessel: Vessel) -> str:
        """Format comprehensive speed information."""
        if not vessel.speed:
            return "Speed: N/A"
        
        speed = vessel.speed
        speed_status = ""
        
        if speed == 0:
            speed_status = " (Stationary)"
        elif speed < 1:
            speed_status = " (Drifting)"
        elif speed < 5:
            speed_status = " (Slow)"
        elif speed > 15:
            speed_status = " (Fast)"
        
        return f"Speed: {speed:.1f} knots{speed_status}"
    
    def format_voyage_info(self, vessel: Vessel) -> Dict[str, str]:
        """Format voyage-related information."""
        info = {}
        
        if vessel.destination:
            info['destination'] = vessel.destination
        else:
            info['destination'] = "Unknown"
        
        if vessel.eta:
            try:
                # Try to parse and format ETA nicely
                info['eta'] = vessel.eta
            except:
                info['eta'] = vessel.eta
        else:
            info['eta'] = "Not available"
        
        return info
    
    def calculate_voyage_progress(self, vessel: Vessel, 
                                  origin_lat: float, origin_lon: float,
                                  dest_lat: float, dest_lon: float) -> Optional[float]:
        """
        Calculate progress along a voyage route.
        
        Returns:
            Percentage complete (0-100) or None
        """
        if not vessel.has_position():
            return None
        
        from math import radians, sin, cos, sqrt, atan2
        
        def distance(lat1, lon1, lat2, lon2):
            R = 6371
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            return R * c
        
        total_distance = distance(origin_lat, origin_lon, dest_lat, dest_lon)
        if total_distance == 0:
            return None
        
        traveled = distance(origin_lat, origin_lon, vessel.lat, vessel.lon)
        progress = (traveled / total_distance) * 100
        
        return min(100, max(0, progress))
    
    def generate_enhanced_popup(self, vessel: Vessel, 
                               nearby_ports: List = None) -> str:
        """
        Generate comprehensive HTML popup for vessel.
        
        Args:
            vessel: Vessel object
            nearby_ports: List of nearby ports
            
        Returns:
            HTML string for popup
        """
        icon = self.get_vessel_icon(vessel)
        ship_type_name = SHIP_TYPE_NAMES.get(vessel.ship_type, f"Type {vessel.ship_type}")
        
        # Determine vessel color based on type and status
        if vessel.is_tanker(TANKER_TYPES):
            header_color = "#C62828"  # Dark red for tankers
        elif vessel.ship_type in range(70, 80):
            header_color = "#F57C00"  # Orange for cargo
        else:
            header_color = "#1976D2"  # Blue for others
        
        html = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; min-width: 280px; max-width: 350px;">
            <div style="background: linear-gradient(135deg, {header_color} 0%, {header_color}CC 100%);
                        color: white; padding: 12px; margin: -10px -10px 10px -10px; 
                        border-radius: 5px 5px 0 0;">
                <h3 style="margin: 0; font-size: 16px; font-weight: 600;">
                    {icon} {vessel.name or f'MMSI {vessel.mmsi}'}
                </h3>
                <div style="font-size: 11px; opacity: 0.9; margin-top: 4px;">
                    {ship_type_name}
                </div>
            </div>
            
            <table style="font-size: 12px; width: 100%; border-collapse: collapse;">
        """
        
        # Identification Section
        html += f"""
                <tr style="background: #f5f5f5;">
                    <td colspan="2" style="padding: 6px 8px; font-weight: 600; border-bottom: 2px solid #ddd;">
                        📋 Identification
                    </td>
                </tr>
                <tr>
                    <td style="padding: 4px 8px; color: #666; width: 40%;">MMSI:</td>
                    <td style="padding: 4px 8px; font-weight: 500;">{vessel.mmsi}</td>
                </tr>
        """
        
        if vessel.imo:
            html += f"""
                <tr>
                    <td style="padding: 4px 8px; color: #666;">IMO:</td>
                    <td style="padding: 4px 8px; font-weight: 500;">{vessel.imo}</td>
                </tr>
            """
        
        if vessel.callsign:
            html += f"""
                <tr>
                    <td style="padding: 4px 8px; color: #666;">Callsign:</td>
                    <td style="padding: 4px 8px; font-weight: 500;">{vessel.callsign}</td>
                </tr>
            """
        
        # Tanker-Specific Information
        if vessel.is_tanker(TANKER_TYPES):
            tanker_class = self.get_tanker_class(vessel)
            capacity = self.estimate_cargo_capacity(vessel)
            
            html += f"""
                <tr style="background: #fff3e0;">
                    <td colspan="2" style="padding: 6px 8px; font-weight: 600; border-bottom: 2px solid #ff9800; color: #e65100;">
                        🛢️ Tanker Details
                    </td>
                </tr>
            """
            
            if tanker_class:
                html += f"""
                <tr style="background: #fffaf0;">
                    <td style="padding: 4px 8px; color: #666;">Class:</td>
                    <td style="padding: 4px 8px; font-weight: 600; color: #e65100;">{tanker_class}</td>
                </tr>
                """
            
            if capacity:
                html += f"""
                <tr style="background: #fffaf0;">
                    <td style="padding: 4px 8px; color: #666;">Capacity:</td>
                    <td style="padding: 4px 8px; font-weight: 500;">{capacity}</td>
                </tr>
                """
        
        # Navigation Section
        html += f"""
                <tr style="background: #e3f2fd;">
                    <td colspan="2" style="padding: 6px 8px; font-weight: 600; border-bottom: 2px solid #2196f3;">
                        🧭 Navigation
                    </td>
                </tr>
        """
        
        speed_info = self.format_speed_info(vessel)
        html += f"""
                <tr>
                    <td style="padding: 4px 8px; color: #666;">Speed:</td>
                    <td style="padding: 4px 8px; font-weight: 500;">{vessel.speed or 'N/A'} knots</td>
                </tr>
                <tr>
                    <td style="padding: 4px 8px; color: #666;">Course:</td>
                    <td style="padding: 4px 8px; font-weight: 500;">{vessel.course or 'N/A'}°</td>
                </tr>
        """
        
        if vessel.heading is not None:
            html += f"""
                <tr>
                    <td style="padding: 4px 8px; color: #666;">Heading:</td>
                    <td style="padding: 4px 8px; font-weight: 500;">{vessel.heading}°</td>
                </tr>
            """
        
        if vessel.navigational_status is not None:
            color, status_text = self.NAV_STATUS_COLORS.get(
                vessel.navigational_status, 
                ('#9E9E9E', 'Unknown')
            )
            html += f"""
                <tr>
                    <td style="padding: 4px 8px; color: #666;">Status:</td>
                    <td style="padding: 4px 8px; font-weight: 500; color: {color};">
                        ● {status_text}
                    </td>
                </tr>
            """
        
        # Voyage Section
        voyage_info = self.format_voyage_info(vessel)
        html += f"""
                <tr style="background: #f3e5f5;">
                    <td colspan="2" style="padding: 6px 8px; font-weight: 600; border-bottom: 2px solid #9c27b0;">
                        🗺️ Voyage
                    </td>
                </tr>
                <tr>
                    <td style="padding: 4px 8px; color: #666;">Destination:</td>
                    <td style="padding: 4px 8px; font-weight: 500;">{voyage_info['destination']}</td>
                </tr>
                <tr>
                    <td style="padding: 4px 8px; color: #666;">ETA:</td>
                    <td style="padding: 4px 8px;">{voyage_info['eta']}</td>
                </tr>
        """
        
        # Nearby Ports
        if nearby_ports:
            html += f"""
                <tr>
                    <td style="padding: 4px 8px; color: #666;">Nearby:</td>
                    <td style="padding: 4px 8px; font-size: 11px;">
            """
            for port, distance in nearby_ports[:2]:  # Show top 2
                html += f"⚓ {port.name} ({distance:.0f}km)<br>"
            html += "</td></tr>"
        
        # Dimensions Section
        if vessel.length or vessel.width or vessel.draught:
            html += f"""
                <tr style="background: #e8f5e9;">
                    <td colspan="2" style="padding: 6px 8px; font-weight: 600; border-bottom: 2px solid #4caf50;">
                        📏 Dimensions
                    </td>
                </tr>
            """
            
            if vessel.length and vessel.width:
                html += f"""
                <tr>
                    <td style="padding: 4px 8px; color: #666;">Size:</td>
                    <td style="padding: 4px 8px; font-weight: 500;">{vessel.length:.0f}m × {vessel.width:.0f}m</td>
                </tr>
                """
            
            if vessel.draught:
                html += f"""
                <tr>
                    <td style="padding: 4px 8px; color: #666;">Draught:</td>
                    <td style="padding: 4px 8px; font-weight: 500;">{vessel.draught:.1f}m</td>
                </tr>
                """
        
        # Position & Tracking
        html += f"""
                <tr style="background: #fce4ec;">
                    <td colspan="2" style="padding: 6px 8px; font-weight: 600; border-bottom: 2px solid #e91e63;">
                        📍 Position & Tracking
                    </td>
                </tr>
                <tr>
                    <td style="padding: 4px 8px; color: #666;">Position:</td>
                    <td style="padding: 4px 8px; font-size: 11px; font-family: monospace;">
                        {vessel.lat:.4f}°, {vessel.lon:.4f}°
                    </td>
                </tr>
                <tr>
                    <td style="padding: 4px 8px; color: #666;">Updates:</td>
                    <td style="padding: 4px 8px;">{vessel.update_count}</td>
                </tr>
                <tr>
                    <td style="padding: 4px 8px; color: #666;">Last seen:</td>
                    <td style="padding: 4px 8px;">{vessel.last_update or 'N/A'}</td>
                </tr>
        """
        
        if vessel.first_seen:
            html += f"""
                <tr>
                    <td style="padding: 4px 8px; color: #666;">First seen:</td>
                    <td style="padding: 4px 8px;">{vessel.first_seen}</td>
                </tr>
            """
        
        html += """
            </table>
        </div>
        """
        
        return html
    
    def generate_vessel_tooltip(self, vessel: Vessel) -> str:
        """Generate concise tooltip for vessel marker."""
        icon = self.get_vessel_icon(vessel)
        name = vessel.name or f"MMSI {vessel.mmsi}"
        
        parts = [f"{icon} {name}"]
        
        if vessel.is_tanker(TANKER_TYPES):
            tanker_class = self.get_tanker_class(vessel)
            if tanker_class:
                parts.append(f"({tanker_class})")
        
        if vessel.speed:
            parts.append(f"{vessel.speed:.1f} kts")
        
        if vessel.destination:
            parts.append(f"→ {vessel.destination}")
        
        return " | ".join(parts)

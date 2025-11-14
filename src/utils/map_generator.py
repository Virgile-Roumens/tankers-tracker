"""
Map generator for visualizing vessel positions using Folium.
"""

import folium
import webbrowser
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging

from config import (REGIONS, PORTS, MAP_TILES, MAP_ZOOM_LEVEL,
                   PORT_MARKER_RADIUS, VESSEL_MARKER_RADIUS,
                   HTML_AUTO_REFRESH_SECONDS, ENABLE_AUTO_REFRESH,
                   PAUSE_ON_USER_ACTIVITY, USER_ACTIVITY_TIMEOUT)
from models.vessel import Vessel
from models.region import Port
from enums.ship_type import ShipType
from enums.region import Region
from utils.enhanced_map_integration import EnhancedMapIntegration

logger = logging.getLogger(__name__)

# Import enhanced display service
try:
    from services.vessel_display_service import VesselDisplayService
    from services.region_manager import RegionManager
    ENHANCED_DISPLAY = True
except ImportError:
    ENHANCED_DISPLAY = False
    logger.warning("Enhanced display services not available, using basic display")


class MapGenerator:
    """
    Generates and updates interactive maps for vessel tracking.
    """
    
    def __init__(self, region_name: str, output_file: str = "tankers_map.html"):
        """
        Initialize map generator.
        
        Args:
            region_name: Name of the region to display
            output_file: Output HTML file path
        """
        self.region_name = region_name
        self.output_file = output_file
        self.region_bounds = REGIONS.get(region_name, [[[-90, -180], [90, 180]]])
        self.ports = PORTS.get(region_name, [])
        
        # Initialize enhanced services if available
        if ENHANCED_DISPLAY:
            self.display_service = VesselDisplayService()
            self.region_manager = RegionManager()
        else:
            self.display_service = None
            self.region_manager = None
        
        # Initialize enhanced map integration (new features)
        self.enhanced_integration = EnhancedMapIntegration()
        
    def create_base_map(self) -> folium.Map:
        """
        Create a worldwide Folium map (always).
        
        Returns:
            Folium Map object
        """
        # Worldwide: show entire world
        center_lat, center_lon = 20, 0
        zoom = 2
        
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom,
            tiles=MAP_TILES,
            prefer_canvas=True
        )
        
        return m
    
    def add_ports(self, m: folium.Map):
        """
        Add port markers to the map.
        
        Args:
            m: Folium Map object
        """
        for port in self.ports:
            folium.CircleMarker(
                [port["lat"], port["lon"]],
                radius=PORT_MARKER_RADIUS,
                popup=f"<b>⚓ {port['name']}</b><br>{port['country']}",
                tooltip=port['name'],
                color='blue',
                fill=True,
                fillColor='lightblue',
                fillOpacity=0.7
            ).add_to(m)
    
    def add_vessels(self, m: folium.Map, vessels: Dict[int, Vessel]):
        """
        Add vessel markers to the map.
        
        Args:
            m: Folium Map object
            vessels: Dictionary of vessels keyed by MMSI
        """
        for mmsi, vessel in vessels.items():
            if vessel.has_position():
                self._add_vessel_marker(m, vessel)
    
    def _add_vessel_marker(self, m: folium.Map, vessel: Vessel):
        """
        Add a single vessel marker to the map with comprehensive information.
        
        Args:
            m: Folium Map object
            vessel: Vessel object
        """
        # Use enhanced display service if available
        if self.display_service and self.region_manager:
            # Get nearby ports
            nearby_ports = self.region_manager.get_nearby_ports(
                vessel.lat, vessel.lon, max_distance_km=50
            )
            
            # Generate enhanced popup
            popup_html = self.display_service.generate_enhanced_popup(
                vessel, nearby_ports
            )
            
            # Generate enhanced tooltip
            tooltip_text = self.display_service.generate_vessel_tooltip(vessel)
            
            # Get vessel icon
            icon = self.display_service.get_vessel_icon(vessel)
            
        else:
            # Fallback to basic display
            ship_type_name = vessel.get_ship_type_name()
            
            # Build comprehensive popup with all available data
            popup_html = f"""
        <div style="font-family: Arial; min-width: 220px;">
            <h4 style="margin: 0 0 8px 0; color: #d32f2f;">
                🛢️ {vessel.name or f'MMSI {vessel.mmsi}'}
            </h4>
            <table style="font-size: 11px; width: 100%;">
                <tr><td><b>Type:</b></td><td>{ship_type_name}</td></tr>
                <tr><td><b>MMSI:</b></td><td>{vessel.mmsi}</td></tr>
        """
        
            # Add IMO if available
            if vessel.imo:
                popup_html += f"<tr><td><b>IMO:</b></td><td>{vessel.imo}</td></tr>"
        
            # Add callsign if available
            if vessel.callsign:
                popup_html += f"<tr><td><b>Callsign:</b></td><td>{vessel.callsign}</td></tr>"
        
            # Navigation info
            popup_html += f"""
                <tr><td colspan="2" style="padding-top: 8px; border-top: 1px solid #ddd;"><b>Navigation</b></td></tr>
                <tr><td><b>Speed:</b></td><td>{vessel.speed or 'N/A'} knots</td></tr>
                <tr><td><b>Course:</b></td><td>{vessel.course or 'N/A'}°</td></tr>
        """
        
            if vessel.heading is not None:
                popup_html += f"<tr><td><b>Heading:</b></td><td>{vessel.heading}°</td></tr>"
        
            if vessel.navigational_status is not None:
                popup_html += f"<tr><td><b>Status:</b></td><td>{vessel.get_navigational_status_text()}</td></tr>"
        
            # Voyage info
            popup_html += f"""
                <tr><td colspan="2" style="padding-top: 8px; border-top: 1px solid #ddd;"><b>Voyage</b></td></tr>
                <tr><td><b>To:</b></td><td>{vessel.destination or 'Unknown'}</td></tr>
        """
        
            if vessel.eta:
                popup_html += f"<tr><td><b>ETA:</b></td><td>{vessel.eta}</td></tr>"
        
            # Vessel dimensions
            if vessel.length or vessel.width:
                popup_html += f"""
                <tr><td colspan="2" style="padding-top: 8px; border-top: 1px solid #ddd;"><b>Dimensions</b></td></tr>
                <tr><td><b>Size:</b></td><td>{vessel.get_dimensions()}</td></tr>
            """
        
            if vessel.draught:
                popup_html += f"<tr><td><b>Draught:</b></td><td>{vessel.draught} m</td></tr>"
        
            # Position and tracking
            popup_html += f"""
                <tr><td colspan="2" style="padding-top: 8px; border-top: 1px solid #ddd;"><b>Position</b></td></tr>
                <tr><td><b>Lat, Lon:</b></td><td>{vessel.lat:.4f}, {vessel.lon:.4f}</td></tr>
                <tr><td><b>Updates:</b></td><td>{vessel.update_count}</td></tr>
                <tr><td><b>Last seen:</b></td><td>{vessel.last_update or 'N/A'}</td></tr>
        """
        
            popup_html += """
            </table>
        </div>
        """
            
            # Create tooltip with key info
            tooltip_text = f"{vessel.name or vessel.mmsi}"
            if vessel.speed:
                tooltip_text += f" | {vessel.speed} kts"
            if vessel.destination:
                tooltip_text += f" → {vessel.destination}"
        
        # ✨ NEW FEATURE: Enhance popup with geolocation information
        popup_html = self.enhanced_integration.enhance_vessel_popup(vessel, popup_html)
        
        # Get color based on ship type
        if vessel.ship_type:
            color = vessel.ship_type.get_color()
        else:
            color = '#808080'  # Gray for unknown type
        
        # ✨ NEW FEATURE: Create directional marker with arrow if vessel is moving
        try:
            if vessel.speed and vessel.speed > 0.5 and vessel.course is not None:
                # Moving vessel - use arrow marker
                heading = int(vessel.course) % 360
                
                # Create arrow SVG
                arrow_svg = f'''
                <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <g transform="rotate({heading} 12 12)">
                        <polygon points="12,3 20,18 12,15 4,18" fill="{color}" stroke="white" stroke-width="1"/>
                        <circle cx="12" cy="12" r="2" fill="white"/>
                    </g>
                </svg>
                '''
                
                # Create marker with HTML icon
                import base64
                svg_bytes = arrow_svg.encode('utf-8')
                svg_base64 = base64.b64encode(svg_bytes).decode('utf-8')
                icon_uri = f"data:image/svg+xml;base64,{svg_base64}"
                
                icon = folium.features.CustomIcon(
                    icon_image=icon_uri,
                    icon_size=(24, 24),
                    icon_anchor=(12, 12),
                    popup_anchor=(0, -12)
                )
                
                marker = folium.Marker(
                    location=[vessel.lat, vessel.lon],
                    popup=folium.Popup(popup_html, max_width=350),
                    tooltip=tooltip_text,
                    icon=icon
                )
            else:
                # Stationary vessel - use circle marker
                marker = folium.CircleMarker(
                    [vessel.lat, vessel.lon],
                    radius=VESSEL_MARKER_RADIUS,
                    popup=folium.Popup(popup_html, max_width=350),
                    tooltip=tooltip_text,
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.9
                )
        except Exception as e:
            # Fallback to circle marker if arrow rendering fails
            logger.debug(f"Arrow marker error for vessel {vessel.mmsi}: {e}")
            marker = folium.CircleMarker(
                [vessel.lat, vessel.lon],
                radius=VESSEL_MARKER_RADIUS,
                popup=folium.Popup(popup_html, max_width=350),
                tooltip=tooltip_text,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.9
            )
        
        # Store MMSI in marker options for JavaScript identification (accessible via layer.options.mmsi)
        marker.options['mmsi'] = vessel.mmsi
        
        marker.add_to(m)
    
    def generate_map(self, vessels: Dict[int, Vessel], auto_open: bool = False):
        """
        Generate complete map with ports and vessels.
        
        Args:
            vessels: Dictionary of vessels keyed by MMSI
            auto_open: Whether to automatically open the map in browser
        """
        # ✨ NEW FEATURE: Initialize enhanced integration with current vessels
        self.enhanced_integration.update_vessels(vessels)
        
        # Count only UNIQUE vessels by MMSI
        unique_mmsi = set(vessels.keys())
        active_vessels = [v for v in vessels.values() if v.has_position()]
        active_count = len(active_vessels)
        tankers = [v for v in active_vessels if v.is_tanker()]
        tanker_count = len(tankers)
        
        # Debug logging
        vessels_with_shiptype = sum(1 for v in active_vessels if v.ship_type is not None)
        vessels_without_shiptype = active_count - vessels_with_shiptype
        
        logger.info(f"\n🗺️  Generating map with {active_count} unique vessels ({tanker_count} tankers)")
        logger.info(f"   📊 Breakdown: {vessels_with_shiptype} with ship_type, {vessels_without_shiptype} WITHOUT ship_type data")
        logger.info(f"   🛢️  Tankers identified: {tanker_count}")
        
        m = self.create_base_map()
        self.add_ports(m)
        self.add_vessels(m, vessels)
        
        # CSS is embedded inline in _create_map_interface, so no external CSS link needed
        # This prevents 404 errors when the static directory isn't accessible
        
        # Add auto-refresh functionality and statistics to map
        title_html = self._create_map_interface(active_count, tanker_count)
        m.get_root().html.add_child(folium.Element(title_html))
        
        # Add cache-busting meta tag to prevent stale map display
        cache_bust_html = '''
        <meta http-equiv="cache-control" content="no-cache, no-store, must-revalidate">
        <meta http-equiv="pragma" content="no-cache">
        <meta http-equiv="expires" content="0">
        '''
        m.get_root().html.add_child(folium.Element(cache_bust_html))
        
        # ✨ NEW FEATURE: Analyze and report on unknown vessels
        try:
            analysis = self.enhanced_integration.analyze_unknown_vessels()
            unknown_count = analysis.get('total_unknown', 0)
            
            if unknown_count > 0:
                logger.warning(f"\n⚠️  UNKNOWN VESSELS DETECTED: {unknown_count} vessels without ship_type classification")
                logger.warning(f"   These vessels need manual investigation or classification")
                
                # Show first few unknown vessels for quick reference
                sample_vessels = analysis.get('vessels', [])[:3]
                for vessel_info in sample_vessels:
                    logger.info(f"      • MMSI {vessel_info['mmsi']}: {vessel_info.get('name', 'Unknown')} "
                               f"({vessel_info.get('water_type', 'Unknown').replace('_', ' ').title()})")
                
                if len(analysis.get('vessels', [])) > 3:
                    logger.info(f"      ... and {len(analysis['vessels']) - 3} more")
            
            # Get vessel statistics
            stats = self.enhanced_integration.get_vessel_statistics()
            logger.info(f"\n📊 VESSEL STATISTICS:")
            logger.info(f"   Total vessels in database: {stats.get('total_vessels', 0)}")
            logger.info(f"   Active (with position): {active_count}")
            logger.info(f"   Stationary vessels: {stats.get('stationary', 0)}")
            logger.info(f"   Fast-moving (>5 knots): {stats.get('moving', 0)}")
            logger.info(f"   Tankers: {tanker_count}")
            logger.info(f"   Unknown types: {unknown_count}\n")
            
        except Exception as e:
            logger.debug(f"Enhanced analysis error (non-critical): {e}")
        
        # Atomic file write to prevent blank page during refresh
        temp_file = f"{self.output_file}.tmp"
        try:
            import time
            max_retries = 10  # Increased from 5
            retry_delay = 0.1  # Start with 100ms
            last_error = None
            
            # First, try to close any existing file handle
            for attempt in range(max_retries):
                try:
                    # Save to temp file
                    m.save(temp_file)
                    time.sleep(0.1)  # Let file system flush
                    
                    # Atomic rename to final file (prevents reading partial file)
                    import os
                    if os.path.exists(self.output_file):
                        # On Windows, we need to remove the target first
                        os.remove(self.output_file)
                        time.sleep(0.05)  # Brief pause
                    
                    os.rename(temp_file, self.output_file)
                    time.sleep(0.05)  # Let file system confirm
                    break  # Success!
                    
                except (PermissionError, OSError, FileNotFoundError) as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        # File is locked, wait and retry
                        time.sleep(retry_delay)
                        retry_delay *= 1.5  # Exponential backoff
                        logger.debug(f"Retry {attempt + 1}/{max_retries}: {e}")
                    else:
                        # Last attempt failed, raise the error
                        raise
            
            # Verify file was written correctly
            import os
            if os.path.exists(self.output_file):
                file_size = os.path.getsize(self.output_file)
                if file_size > 1000:  # Sanity check: HTML should be > 1KB
                    logger.info(f"✅ Map saved to {self.output_file} ({file_size:,} bytes)\n")
                else:
                    logger.warning(f"⚠️  Map file seems small ({file_size} bytes), may be incomplete!")
            else:
                raise FileNotFoundError(f"Map file {self.output_file} not found after save!")
                
        except Exception as e:
            logger.error(f"Failed to save map: {e}")
            # Clean up temp file if it exists
            import os
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass  # Best effort cleanup
            raise
        
        if auto_open:
            self.open_map()
    
    def _create_map_interface(self, active_count: int, tanker_count: int) -> str:
        """
        Create the map interface HTML with auto-refresh functionality (worldwide only).
        
        Args:
            active_count: Number of active vessels
            tanker_count: Number of active tankers
            
        Returns:
            HTML string for the map interface
        """
        refresh_status = "enabled" if ENABLE_AUTO_REFRESH else "disabled"
        refresh_interval = HTML_AUTO_REFRESH_SECONDS if ENABLE_AUTO_REFRESH else 0
        
        # Modern control panel HTML
        # Include minimal inline CSS to guarantee floating overlays even if external CSS fails to load
        title_html = f'''
        <style>
            /* Ensure map fills screen and overlays float */
            html, body {{ margin: 0; padding: 0; height: 100%; }}
            #map {{ position: absolute; top: 0; left: 0; height: 100%; width: 100%; }}
            .control-panel {{
                position: fixed;
                    top: 10px; 
                right: 10px;
                z-index: 1000;
                    width: 320px; 
                border-radius: 6px;
                background: rgba(255, 255, 255, 0.98);
                backdrop-filter: blur(10px);
                color: #1a1a1a;
                padding: 0;
                box-shadow: 0 4px 20px rgba(0,0,0,0.12);
                border: 1px solid rgba(0,0,0,0.08);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            }}
            .control-panel-header {{
                padding: 14px 16px;
                border-bottom: 1px solid rgba(0,0,0,0.08);
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: linear-gradient(to bottom, rgba(249,250,251,1), rgba(255,255,255,1));
            }}
            .control-panel-title {{
                font-size: 14px;
                font-weight: 600;
                color: #1a1a1a;
                letter-spacing: -0.2px;
            }}
            .filter-panel {{
                position: fixed;
                top: 130px;
                right: 10px;
                z-index: 1100;
                width: 320px;
                max-height: calc(100vh - 380px);
                overflow-y: auto;
                border-radius: 6px;
                background: rgba(255, 255, 255, 0.98);
                backdrop-filter: blur(10px);
                box-shadow: 0 4px 20px rgba(0,0,0,0.12);
                border: 1px solid rgba(0,0,0,0.08);
                display: none;
            }}
            .filter-panel.visible {{
                display: block;
            }}
            .filter-header {{
                background: linear-gradient(to bottom, rgba(249,250,251,1), rgba(255,255,255,1));
                color: #1a1a1a;
                padding: 14px 16px;
                font-weight: 600;
                font-size: 14px;
                border-bottom: 1px solid rgba(0,0,0,0.08);
                display: flex;
                justify-content: space-between;
                align-items: center;
                letter-spacing: -0.2px;
            }}
            .filter-content {{
                padding: 16px;
            }}
            .filter-group {{
                margin-bottom: 16px;
            }}
            .filter-group:last-of-type {{
                margin-bottom: 0;
            }}
            .filter-group-title {{
                font-weight: 600;
                font-size: 10px;
                color: #6b7280;
                text-transform: uppercase;
                margin-bottom: 10px;
                letter-spacing: 0.8px;
            }}
            .filter-option {{
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 8px;
                padding: 4px 0;
            }}
            .filter-option label {{
                font-size: 14px;
                cursor: pointer;
                flex: 1;
                color: #374151;
                font-weight: 400;
            }}
            .filter-option input[type="checkbox"] {{
                cursor: pointer;
                width: 18px;
                height: 18px;
                accent-color: #2563eb;
            }}
            .filter-buttons {{
                display: flex;
                gap: 8px;
                padding: 16px;
                background: rgba(249,250,251,0.5);
                border-top: 1px solid rgba(0,0,0,0.06);
                margin: 0 -16px -16px -16px;
                border-radius: 0 0 6px 6px;
            }}
            .filter-buttons button {{
                flex: 1;
                padding: 10px 16px;
                border: none;
                    border-radius: 5px;
                font-weight: 500;
                cursor: pointer;
                font-size: 13px;
                transition: all 0.2s;
            }}
            .filter-buttons button:first-child {{
                background: #2563eb;
                color: white;
            }}
            .filter-buttons button:first-child:hover {{
                background: #1d4ed8;
            }}
            .filter-buttons button:last-child {{
                background: rgba(0,0,0,0.05);
                color: #374151;
            }}
            .filter-buttons button:last-child:hover {{
                background: rgba(0,0,0,0.08);
            }}
            .legend {{
                position: fixed;
                bottom: 20px;
                right: 10px;
                z-index: 1100;
                border-radius: 6px;
                background: rgba(255, 255, 255, 0.98);
                backdrop-filter: blur(10px);
                box-shadow: 0 4px 20px rgba(0,0,0,0.12);
                border: 1px solid rgba(0,0,0,0.08);
                width: 320px;
            }}
            .legend-header {{
                background: linear-gradient(to bottom, rgba(249,250,251,1), rgba(255,255,255,1));
                color: #1a1a1a;
                padding: 14px 16px;
                font-weight: 600;
                font-size: 14px;
                border-bottom: 1px solid rgba(0,0,0,0.08);
                display: flex;
                justify-content: space-between;
                align-items: center;
                cursor: pointer;
                letter-spacing: -0.2px;
            }}
            .legend-content {{
                padding: 16px;
                display: block;
            }}
            .legend-content.collapsed {{
                display: none;
            }}
            .legend-dot {{
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 10px;
                border: 2px solid rgba(0,0,0,0.1);
            }}
            .legend-item {{
                display: flex;
                align-items: center;
                margin-bottom: 10px;
                font-size: 13px;
                color: #374151;
            }}
            .legend-item:last-child {{
                margin-bottom: 0;
            }}
            .panel-toggle {{
                background: transparent;
                border: none;
                color: #6b7280;
                font-size: 16px;
                line-height: 1;
                padding: 4px 8px;
                border-radius: 4px;
                cursor: pointer;
                transition: all 0.2s;
            }}
            .panel-toggle:hover {{
                background: rgba(0,0,0,0.05);
                color: #1a1a1a;
            }}
            .stats-row {{
                display: flex;
                gap: 16px;
                padding: 14px 16px;
                border-bottom: 1px solid rgba(0,0,0,0.06);
            }}
            .stat-item {{
                flex: 1;
            }}
            .stat-label {{
                font-size: 10px;
                text-transform: uppercase;
                color: #6b7280;
                font-weight: 600;
                letter-spacing: 0.8px;
                margin-bottom: 4px;
            }}
            .stat-value {{
                font-size: 20px;
                font-weight: 700;
                color: #1a1a1a;
                letter-spacing: -0.5px;
            }}
            .status-row {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 12px 16px;
                border-bottom: 1px solid rgba(0,0,0,0.06);
            }}
            .status-badge {{
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 12px;
                color: #374151;
            }}
            .status-dot {{
                width: 6px;
                height: 6px;
                border-radius: 50%;
                background: #10b981;
                animation: pulse 2s infinite;
            }}
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.5; }}
            }}
            .action-buttons {{
                display: flex;
                gap: 8px;
                padding: 12px 16px;
            }}
            .btn {{
                flex: 1;
                padding: 8px 12px;
                border: none;
                border-radius: 5px;
                font-weight: 500;
                cursor: pointer;
                font-size: 12px;
                transition: all 0.2s;
                text-align: center;
            }}
            .btn-primary {{
                background: #2563eb;
                color: white;
            }}
            .btn-primary:hover {{
                background: #1d4ed8;
            }}
            .btn-secondary {{
                background: rgba(0,0,0,0.05);
                color: #374151;
            }}
            .btn-secondary:hover {{
                background: rgba(0,0,0,0.08);
            }}
            .btn-warning {{
                background: #f59e0b;
                color: white;
            }}
            .btn-warning:hover {{
                background: #d97706;
            }}
            .btn-success {{
                background: #10b981;
                color: white;
            }}
            .btn-success:hover {{
                background: #059669;
            }}
            .control-panel.collapsed .stats-row,
            .control-panel.collapsed .status-row,
            .control-panel.collapsed .action-buttons {{
                display: none;
            }}
            .search-bar {{
                position: fixed;
                bottom: 20px;
                left: 10px;
                z-index: 1100;
                width: 360px;
                border-radius: 6px;
                background: rgba(255, 255, 255, 0.98);
                backdrop-filter: blur(10px);
                box-shadow: 0 4px 20px rgba(0,0,0,0.12);
                border: 1px solid rgba(0,0,0,0.08);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            }}
            .search-header {{
                background: linear-gradient(to bottom, rgba(249,250,251,1), rgba(255,255,255,1));
                color: #1a1a1a;
                padding: 14px 16px;
                font-weight: 600;
                font-size: 14px;
                border-bottom: 1px solid rgba(0,0,0,0.08);
                letter-spacing: -0.2px;
            }}
            .search-content {{
                padding: 16px;
            }}
            .search-input-group {{
                display: flex;
                gap: 8px;
                align-items: center;
            }}
            .search-input {{
                flex: 1;
                padding: 10px 14px;
                border: 1px solid rgba(0,0,0,0.12);
                border-radius: 5px;
                font-size: 14px;
                color: #1a1a1a;
                background: white;
                transition: all 0.2s;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            }}
            .search-input:focus {{
                outline: none;
                border-color: #2563eb;
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
            }}
            .search-input::placeholder {{
                color: #9ca3af;
            }}
            .search-btn {{
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                background: #2563eb;
                color: white;
                font-weight: 500;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.2s;
                white-space: nowrap;
            }}
            .search-btn:hover {{
                background: #1d4ed8;
            }}
            .search-btn:active {{
                transform: scale(0.98);
            }}
            .search-message {{
                margin-top: 12px;
                padding: 10px;
                border-radius: 5px;
                font-size: 13px;
                text-align: center;
                display: none;
            }}
            .search-message.success {{
                background: rgba(16, 185, 129, 0.1);
                color: #059669;
                border: 1px solid rgba(16, 185, 129, 0.2);
            }}
            .search-message.error {{
                background: rgba(239, 68, 68, 0.1);
                color: #dc2626;
                border: 1px solid rgba(239, 68, 68, 0.2);
            }}
        </style>
        <div class="control-panel" id="control-panel">
            <div class="control-panel-header">
                <div class="control-panel-title">Strategic Tanker Tracker</div>
                <button class="panel-toggle" onclick="toggleControlPanel()" title="Toggle panel">−</button>
        </div>
            
            <div class="stats-row">
                <div class="stat-item">
                    <div class="stat-label">Active Vessels</div>
                    <div class="stat-value">{active_count}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Tankers</div>
                    <div class="stat-value" style="color: #dc2626;">{tanker_count}</div>
                </div>
            </div>
            
            <div class="status-row">
                <div class="status-badge">
                    <div class="status-dot"></div>
                    <span>Live Tracking</span>
                </div>
                <button class="btn btn-secondary" style="flex: 0; padding: 6px 12px;" onclick="toggleFilterPanel()" title="Toggle filters">Filters</button>
            </div>
            
            <div class="action-buttons">
        '''
        
        if ENABLE_AUTO_REFRESH:
            title_html += f'''
                <button id="pause-btn" class="btn btn-warning" onclick="toggleAutoRefresh()" title="Pause auto-refresh">Pause</button>
                <button id="refresh-btn" class="btn btn-success" onclick="manualRefresh()" title="Refresh now">Refresh</button>
            '''
        
        title_html += '''
            </div>
        </div>
        
        <!-- Filter Panel -->
        <div class="filter-panel" id="filter-panel">
            <div class="filter-header">
                Filter Vessels
                <button class="panel-toggle" onclick="toggleFilterPanel()" title="Close">✕</button>
            </div>
            <div class="filter-content">
                <!-- Vessel Type Filter -->
                <div class="filter-group">
                    <div class="filter-group-title">Vessel Type</div>
                    <div class="filter-option">
                        <input type="checkbox" id="filter-tankers" checked>
                        <label for="filter-tankers">Oil Tankers</label>
                    </div>
                    <div class="filter-option">
                        <input type="checkbox" id="filter-cargo" checked>
                        <label for="filter-cargo">Cargo Ships</label>
                    </div>
                    <div class="filter-option">
                        <input type="checkbox" id="filter-other" checked>
                        <label for="filter-other">Other Vessels</label>
                    </div>
                </div>
                
                <!-- Note: Additional filters removed - vessel metadata not available in current implementation -->
                
                <!-- Action Buttons -->
                <div class="filter-buttons">
                    <button class="filter-btn filter-btn-apply" onclick="applyFilters()">Apply</button>
                    <button class="filter-btn filter-btn-reset" onclick="resetFilters()">Reset</button>
                </div>
            </div>
        </div>
        
        <!-- Legend -->
        <div class="legend" id="legend">
            <div class="legend-header" onclick="toggleLegend()">
                Legend
                <button class="panel-toggle" onclick="event.stopPropagation(); toggleLegend();" title="Toggle legend">−</button>
            </div>
            <div class="legend-content" id="legend-content">
                <div class="legend-item">
                    <span class="legend-dot" style="background: #d32f2f;"></span>
                    <span>Oil Tanker</span>
                </div>
                <div class="legend-item">
                    <span class="legend-dot" style="background: #1976d2;"></span>
                    <span>Cargo Ship</span>
                </div>
                <div class="legend-item">
                    <span class="legend-dot" style="background: #388e3c;"></span>
                    <span>Other Vessel</span>
                </div>
                <div class="legend-item">
                    <span class="legend-dot" style="background: #64b5f6;"></span>
                    <span>Port Terminal</span>
                </div>
            </div>
        </div>
        
        <!-- Search Bar -->
        <div class="search-bar" id="search-bar">
            <div class="search-header">
                Search by MMSI
            </div>
            <div class="search-content">
                <div class="search-input-group">
                    <input type="text" 
                           id="mmsi-search-input" 
                           class="search-input" 
                           placeholder="Enter MMSI number...">
                    <button id="mmsi-search-btn" class="search-btn">Search</button>
                </div>
                <div id="search-message" class="search-message"></div>
            </div>
        </div>
        '''
        
        # Add filter and basic JavaScript functionality
        filter_script = '''
        <script>
            // Define searchByMMSI function - ROBUST IMPLEMENTATION
            window.searchByMMSI = function() {
                try {
                    console.log('🔍 searchByMMSI called');
                    const input = document.getElementById('mmsi-search-input');
                    const messageDiv = document.getElementById('search-message');
                    
                    if (!input || !messageDiv) {
                        console.error('❌ Search elements not found');
                        return;
                    }
                    
                    const mmsi = input.value.trim();
                    console.log('📝 User entered MMSI:', mmsi);
                    
                    // Show loading
                    messageDiv.style.display = 'none';
                    messageDiv.className = 'search-message';
                    
                    if (!mmsi) {
                        messageDiv.textContent = '⚠️ Please enter an MMSI number';
                        messageDiv.className = 'search-message error';
                        messageDiv.style.display = 'block';
                        return;
                    }
                    
                    if (!/^\\d+$/.test(mmsi)) {
                        messageDiv.textContent = '⚠️ MMSI must be a number';
                        messageDiv.className = 'search-message error';
                        messageDiv.style.display = 'block';
                        return;
                    }
                    
                    const mmsiNum = parseInt(mmsi);
                    console.log('🔢 Searching for MMSI:', mmsiNum);
                    
                    // Find the map
                    const map = findLeafletMap();
                    if (!map) {
                        console.error('❌ Map not found');
                        messageDiv.textContent = '❌ Map not ready - refresh page';
                        messageDiv.className = 'search-message error';
                        messageDiv.style.display = 'block';
                        return;
                    }
                    
                    // Search all markers
                    let foundMarker = null;
                    const markerCount = Object.keys(map._layers || {}).length;
                    console.log('🗺️ Searching through', markerCount, 'layers');
                    
                    Object.values(map._layers || {}).forEach(layer => {
                        if (layer && layer.options && layer.options.mmsi === mmsiNum) {
                            foundMarker = layer;
                            console.log('✅ Found marker!', mmsiNum);
                        }
                    });
                    
                    // Fallback: search popup content
                    if (!foundMarker) {
                        Object.values(map._layers || {}).forEach(layer => {
                            if (layer && layer._popup && layer._popup._content) {
                                const content = layer._popup._content.toString();
                                if (content.includes('MMSI') && content.includes(mmsi)) {
                                    foundMarker = layer;
                                    if (layer.options) layer.options.mmsi = mmsiNum;
                                    console.log('✅ Found via popup content:', mmsiNum);
                                }
                            }
                        });
                    }
                    
                    if (!foundMarker) {
                        console.log('❌ Vessel not found:', mmsiNum);
                        messageDiv.textContent = `❌ MMSI ${mmsi} not found`;
                        messageDiv.className = 'search-message error';
                        messageDiv.style.display = 'block';
                        return;
                    }
                    
                    // Show marker
                    if (!map.hasLayer(foundMarker)) {
                        foundMarker.addTo(map);
                    }
                    
                    const latlng = foundMarker.getLatLng();
                    console.log('📍 Zooming to:', latlng);
                    
                    map.setView(latlng, 13, {animate: true});
                    
                    if (foundMarker.openPopup) {
                        foundMarker.openPopup();
                    }
                    
                    messageDiv.textContent = `✅ Found MMSI: ${mmsi}`;
                    messageDiv.className = 'search-message success';
                    messageDiv.style.display = 'block';
                    
                    console.log('✨ Search complete');
                    
                    setTimeout(() => {
                        messageDiv.style.display = 'none';
                    }, 4000);
                } catch (err) {
                    console.error('🔴 Search error:', err);
                }
            };
            
            // Global registry to store all vessel markers by MMSI (even when removed from map)
            // Format: { mmsi: marker_layer }
            window.allVesselMarkers = {};
            
            // Store map reference globally when page loads
            window.addEventListener('load', function() {
                setTimeout(function() {
                    // Find the map object in the global scope
                    for (let key in window) {
                        try {
                            if (window[key] && window[key]._layers && typeof window[key].addLayer === 'function') {
                                window.globalMapObject = window[key];
                                console.log('✅ Map object found and stored globally:', key);
                                
                                // Clear and re-initialize marker registry with all current markers
                                window.allVesselMarkers = {};
                                const map = window.globalMapObject;
                                
                                // First, remove any duplicate markers by MMSI
                                const mmsiMap = new Map();
                                const layersToRemove = [];
                                
                                Object.values(map._layers).forEach(layer => {
                                    if (layer instanceof L.CircleMarker) {
                                        const mmsi = layer.options?.mmsi;
                                        const color = layer.options.color?.toLowerCase() || '';
                                        
                                        // Only process vessel markers, not ports
                                        if (!(color === 'blue' || color.includes('#64b5f6') || color.includes('lightblue'))) {
                                            if (mmsi) {
                                                // If we already have a marker for this MMSI, mark the duplicate for removal
                                                if (mmsiMap.has(mmsi)) {
                                                    layersToRemove.push(layer);
                                                } else {
                                                    mmsiMap.set(mmsi, layer);
                                                    window.allVesselMarkers[mmsi] = layer;
                                                }
                                            } else {
                                                // Marker without MMSI - register it but log a warning
                                                console.warn('Marker found without MMSI:', layer);
                                                window.allVesselMarkers['unknown_' + Object.keys(window.allVesselMarkers).length] = layer;
                                            }
                                        }
                                    }
                                });
                                
                                // Remove duplicate markers
                                layersToRemove.forEach(layer => {
                                    if (map.hasLayer(layer)) {
                                        map.removeLayer(layer);
                                    }
                                });
                                
                                if (layersToRemove.length > 0) {
                                    console.log('🗑️ Removed ' + layersToRemove.length + ' duplicate markers');
                                }
                                
                                // Post-process: Extract MMSI from popup content if not in options
                                // This handles cases where Folium didn't serialize the custom option
                                Object.values(window.allVesselMarkers).forEach(layer => {
                                    if (!layer.options.mmsi && layer._popup) {
                                        try {
                                            const popupContent = layer._popup._content;
                                            // Try to extract MMSI from popup HTML (look for "MMSI:</td><td>123456789")
                                            const mmsiMatch = popupContent.match(/MMSI[^>]*>[\s]*(\d+)/i);
                                            if (mmsiMatch && mmsiMatch[1]) {
                                                layer.options.mmsi = parseInt(mmsiMatch[1]);
                                                console.log('Extracted MMSI from popup:', layer.options.mmsi);
                                            }
                                        } catch (e) {
                                            // Ignore errors
                                        }
                                    }
                                });
                                
                                console.log('✅ Registered ' + Object.keys(window.allVesselMarkers).length + ' unique vessel markers');
                                break;
                            }
                        } catch (e) {
                            // Skip cross-origin errors
                        }
                    }
                }, 500); // Small delay to ensure map is initialized
            });
            
            // Panel Management
            function toggleControlPanel() {
                const panel = document.getElementById('control-panel');
                const btn = panel.querySelector('.panel-toggle');
                if (panel.classList.contains('collapsed')) {
                    panel.classList.remove('collapsed');
                    if (btn) btn.textContent = '−';
                } else {
                    panel.classList.add('collapsed');
                    if (btn) btn.textContent = '+';
                }
            }
            
            function toggleFilterPanel() {
                const panel = document.getElementById('filter-panel');
                if (panel) {
                    panel.classList.toggle('visible');
                }
            }
            
            function toggleLegend() {
                const content = document.getElementById('legend-content');
                const btn = document.querySelector('#legend .panel-toggle');
                if (content.classList.contains('collapsed')) {
                    content.classList.remove('collapsed');
                    if (btn) btn.textContent = '−';
                } else {
                    content.classList.add('collapsed');
                    if (btn) btn.textContent = '+';
                }
            }
            
            // Apply filters
            function applyFilters() {
                const filters = {
                    tankers: document.getElementById('filter-tankers')?.checked ?? true,
                    cargo: document.getElementById('filter-cargo')?.checked ?? true,
                    other: document.getElementById('filter-other')?.checked ?? true
                };
                
                // Save filters to localStorage
                localStorage.setItem('vesselFilters', JSON.stringify(filters));
                
                // Apply filter visibility to Folium markers
                applyMarkerFilters(filters);
                
                console.log('Filters applied:', filters);
            }
            
            // Reset filters
            function resetFilters() {
                document.getElementById('filter-tankers').checked = true;
                document.getElementById('filter-cargo').checked = true;
                document.getElementById('filter-other').checked = true;
                
                localStorage.removeItem('vesselFilters');
                console.log('Filters reset to defaults');
                
                // Apply the reset filters (show all)
                applyFilters();
            }
            
            // Find the Leaflet map instance
            function findLeafletMap() {
                // Method 1: Use the globally stored map object
                if (window.globalMapObject) {
                    return window.globalMapObject;
                }
                
                // Method 2: Search window properties for map objects
                for (let key in window) {
                    try {
                        if (window[key] && window[key]._layers && typeof window[key].addLayer === 'function') {
                            console.log('Found map via window search:', key);
                            window.globalMapObject = window[key]; // Cache it
                            return window[key];
                        }
                    } catch (e) {
                        // Skip inaccessible properties (cross-origin)
                        continue;
                    }
                }
                
                // Method 3: Find map div and search its associated map
                const mapDivs = document.querySelectorAll('.folium-map');
                for (let div of mapDivs) {
                    if (div._leaflet_id) {
                        // Search for map with matching ID
                        for (let key in window) {
                            try {
                                if (window[key] && window[key]._container === div) {
                                    console.log('Found map via container match:', key);
                                    window.globalMapObject = window[key]; // Cache it
                                    return window[key];
                                }
                            } catch (e) {
                                continue;
                            }
                        }
                    }
                }
                
                console.error('Could not find map object in any method');
                return null;
            }
            
            // Apply marker filters
            function applyMarkerFilters(filters) {
                try {
                    const map = findLeafletMap();
                    
                    if (!map) {
                        console.error('Could not find Leaflet map instance');
                        alert('Map not found. Please refresh the page and try again.');
                        return;
                    }
                    
                    // Initialize marker registry if not already done
                    if (!window.allVesselMarkers || Object.keys(window.allVesselMarkers).length === 0) {
                        window.allVesselMarkers = {};
                        Object.values(map._layers).forEach(layer => {
                            if (layer instanceof L.CircleMarker) {
                                const mmsi = layer.options?.mmsi;
                                const color = layer.options.color?.toLowerCase() || '';
                                // Only store vessel markers, not ports
                                if (!(color === 'blue' || color.includes('#64b5f6') || color.includes('lightblue'))) {
                                    if (mmsi) {
                                        window.allVesselMarkers[mmsi] = layer;
                                    }
                                }
                            }
                        });
                        console.log('Initialized marker registry with ' + Object.keys(window.allVesselMarkers).length + ' markers');
                    }
                    
                    // Remove any duplicate markers currently on the map (by MMSI)
                    const mmsiOnMap = new Map();
                    Object.values(map._layers).forEach(layer => {
                        if (layer instanceof L.CircleMarker) {
                            const mmsi = layer.options?.mmsi;
                            const color = layer.options.color?.toLowerCase() || '';
                            if (mmsi && !(color === 'blue' || color.includes('#64b5f6') || color.includes('lightblue'))) {
                                if (mmsiOnMap.has(mmsi)) {
                                    // Duplicate found - remove the older one (keep the one already in registry)
                                    const existingLayer = mmsiOnMap.get(mmsi);
                                    if (map.hasLayer(existingLayer)) {
                                        map.removeLayer(existingLayer);
                                    }
                                }
                                mmsiOnMap.set(mmsi, layer);
                            }
                        }
                    });
                    
                    console.log('Found map with ' + Object.keys(map._layers).length + ' layers');
                    console.log('Registry has ' + Object.keys(window.allVesselMarkers).length + ' vessel markers');
                    console.log('Filters being applied:', filters);
                    
                    let hiddenCount = 0;
                    let shownCount = 0;
                    let portCount = 0;
                    let tankerCount = 0;
                    let cargoCount = 0;
                    let otherCount = 0;
                    
                    // Process all vessel markers from registry (not just those currently on map)
                    Object.values(window.allVesselMarkers).forEach(layer => {
                        if (!(layer instanceof L.CircleMarker)) {
                            return; // Skip invalid entries
                        }
                        
                        const color = layer.options.color?.toLowerCase() || '';
                        let shouldShow = true;
                        let vesselType = 'unknown';
                        
                        // Check vessel type filter
                        if (color.includes('#d32f2f') || color.includes('#b71c1c') || 
                            color.includes('#dc143c') || color.includes('#8b0000') ||
                            color.includes('red') || color.includes('crimson')) {
                            vesselType = 'tanker';
                            shouldShow = filters.tankers;
                            tankerCount++;
                        }
                        else if (color.includes('#1976d2') || color.includes('#ff8c00') || 
                                 color.includes('#e65100') || color.includes('#ff6347') ||
                                 color.includes('orange') || color.includes('tomato')) {
                            vesselType = 'cargo';
                            shouldShow = filters.cargo;
                            cargoCount++;
                        }
                        else {
                            vesselType = 'other';
                            shouldShow = filters.other;
                            otherCount++;
                        }
                        
                        // Apply visibility
                        if (shouldShow) {
                            // Check if there's already a marker for this MMSI on the map
                            const mmsi = layer.options?.mmsi;
                            let duplicateFound = false;
                            
                            if (mmsi) {
                                Object.values(map._layers).forEach(existingLayer => {
                                    if (existingLayer instanceof L.CircleMarker && 
                                        existingLayer !== layer &&
                                        existingLayer.options?.mmsi === mmsi) {
                                        duplicateFound = true;
                                        // Remove the duplicate (keep the one from registry)
                                        if (map.hasLayer(existingLayer)) {
                                            map.removeLayer(existingLayer);
                                        }
                                    }
                                });
                            }
                            
                            // Ensure layer is on the map (only if not already there)
                            if (!map.hasLayer(layer)) {
                                layer.addTo(map);
                            }
                            shownCount++;
                        } else {
                            // Remove layer from map
                            if (map.hasLayer(layer)) {
                                map.removeLayer(layer);
                            }
                            hiddenCount++;
                        }
                    });
                    
                    // Count ports separately (always visible)
                    Object.values(map._layers).forEach(layer => {
                        if (layer instanceof L.CircleMarker) {
                            const color = layer.options.color?.toLowerCase() || '';
                            if (color === 'blue' || color.includes('#64b5f6') || color.includes('lightblue')) {
                                portCount++;
                            }
                        }
                    });
                    
                    console.log(`✅ Filters applied:`);
                    console.log(`   Total: ${shownCount} shown, ${hiddenCount} hidden`);
                    console.log(`   Tankers: ${tankerCount}, Cargo: ${cargoCount}, Other: ${otherCount}, Ports: ${portCount}`);
                    
                    // Show result without alert (less annoying)
                    const statusBadge = document.querySelector('.status-badge span');
                    if (statusBadge) {
                        const originalText = statusBadge.textContent;
                        statusBadge.textContent = `${shownCount} vessels shown`;
                        setTimeout(() => {
                            statusBadge.textContent = originalText;
                        }, 3000);
                    }
                } catch (e) {
                    console.error('Filter error:', e);
                    console.error('Error stack:', e.stack);
                    alert('Error applying filters: ' + e.message);
                }
            }
            
            // Load filters from localStorage on page load
            function loadSavedFilters() {
                const saved = localStorage.getItem('vesselFilters');
                if (saved) {
                    try {
                        const filters = JSON.parse(saved);
                        Object.entries(filters).forEach(([key, value]) => {
                            const elem = document.getElementById('filter-' + key);
                            if (elem) {
                                elem.checked = value;
                            }
                        });
                        // Apply saved filters after a short delay to ensure map is ready
                        setTimeout(() => {
                            applyFilters();
                        }, 1000);
                    } catch (e) {
                        console.warn('Could not load saved filters:', e);
                    }
                }
            }
            
            // Initialize on page load
            document.addEventListener('DOMContentLoaded', loadSavedFilters);
            
            // Keyboard shortcut: F to toggle filters (only if not focused in input)
            document.addEventListener('keydown', function(e) {
                if (e.key === 'f' && e.ctrlKey && !document.activeElement.matches('input, textarea')) {
                    e.preventDefault();
                    toggleFilterPanel();
                }
            });
            
            
            // Also set up event listeners for better compatibility
            document.addEventListener('DOMContentLoaded', function() {
                const searchBtn = document.getElementById('mmsi-search-btn');
                const searchInput = document.getElementById('mmsi-search-input');
                
                if (searchBtn) {
                    searchBtn.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        console.log('Search button clicked');
                        if (window.searchByMMSI) {
                            window.searchByMMSI();
                        } else {
                            console.error('searchByMMSI function not found');
                            alert('Search function not loaded. Please refresh the page.');
                        }
                    });
                }
                
                if (searchInput) {
                    searchInput.addEventListener('keypress', function(e) {
                        if (e.key === 'Enter') {
                            e.preventDefault();
                            if (window.searchByMMSI) {
                                window.searchByMMSI();
                            }
                        }
                    });
                }
            });
        </script>
        '''
        
        title_html += filter_script
        
        # Add JavaScript for auto-refresh functionality
        if ENABLE_AUTO_REFRESH:
            script_html = f'''
            <script>
                // Auto-refresh configuration
                let refreshInterval = {refresh_interval};
                let countdown = refreshInterval;
                let isPaused = false;
                let userActive = false;
                let activityTimeout;
                let countdownTimer;
                let isRefreshing = false;
                
                // Region change function
                async function changeRegion() {{
                    const selector = document.getElementById('region-selector');
                    const newRegion = selector.value;
                    
                    console.log('Changing region to:', newRegion);
                    updateStatus('Switching region...', '#ff9800');
                    
                    // Pause auto-refresh during region change
                    isPaused = true;
                    
                    try {{
                        // Call backend API to change region
                        const response = await fetch('/api/change-region', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{ region: newRegion }})
                        }});
                        
                        if (response.ok) {{
                            updateStatus('Region changed! Reloading...', '#4caf50');
                            // Wait for the tracker to restart and file to be ready
                            setTimeout(() => {{
                                window.location.reload(true);
                            }}, 4000);  // Increased to 4 seconds to ensure tracker has restarted
                        }} else {{
                            updateStatus('Region change failed', '#f44336');
                            console.error('Region change failed:', response);
                        }}
                    }} catch (error) {{
                        console.error('Error changing region:', error);
                        updateStatus('Error - server not running?', '#f44336');
                        alert('Could not change region. Make sure the web server is running.\\nUse: python launcher.py');
                    }}
                }}
                
                // Update status indicator
                function updateStatus(message, color = '#4caf50') {{
                    const statusElement = document.getElementById('status-indicator');
                    if (statusElement) {{
                        statusElement.textContent = '● ' + message;
                        statusElement.style.color = color;
                    }}
                }}
                
                // Helper function to reset refresh button state
                function resetRefreshButton() {{
                    const refreshBtn = document.getElementById('refresh-btn');
                    if (refreshBtn) {{
                        refreshBtn.disabled = false;
                        refreshBtn.textContent = 'Refresh';
                        refreshBtn.style.background = '#4caf50';
                    }}
                    isRefreshing = false;
                }}
                
                // Safe reload function with error handling
                function safeReload() {{
                    if (isRefreshing) {{
                        console.log('Refresh already in progress, skipping...');
                        updateStatus('Refresh in progress...', '#ff9800');
                        return;
                    }}
                    
                    isRefreshing = true;
                    console.log('Initiating safe page refresh...');
                    
                    // Update UI indicators
                    const countdownElement = document.getElementById('countdown');
                    const refreshBtn = document.getElementById('refresh-btn');
                    
                    if (countdownElement) {{
                        countdownElement.textContent = 'Loading...';
                    }}
                    if (refreshBtn) {{
                        refreshBtn.disabled = true;
                        refreshBtn.textContent = 'Loading...';
                        refreshBtn.style.background = '#ccc';
                    }}
                    
                    updateStatus('Refreshing...', '#2196f3');
                    
                    // Safety timeout to re-enable button if reload doesn't happen
                    const safetyTimeout = setTimeout(() => {{
                        console.warn('Reload timeout - re-enabling refresh button');
                        resetRefreshButton();
                        updateStatus('Reload timeout - click Refresh again', '#ff9800');
                    }}, 5000); // 5 second safety timeout
                    
                    // Create a delay to ensure map generation is complete
                    setTimeout(() => {{
                        try {{
                            // Clear safety timeout since we're reloading
                            clearTimeout(safetyTimeout);
                            
                            // Use browser's native reload - most reliable method
                            // For http:// protocol, add cache-busting query parameter
                            if (window.location.protocol === 'file:') {{
                                // For file:// protocol, simple reload
                                window.location.reload();
                            }} else {{
                                // For http:// protocol, reload with cache bust using current pathname
                                // This preserves the correct path and avoids 404 errors
                                const pathname = window.location.pathname || '/tankers_map.html';
                                const separator = pathname.includes('?') ? '&' : '?';
                                window.location.href = pathname + separator + '_=' + Date.now();
                            }}
                        }} catch (error) {{
                            console.error('Refresh failed:', error);
                            clearTimeout(safetyTimeout);
                            resetRefreshButton();
                            updateStatus('Refresh failed - click Refresh again', '#f44336');
                            
                            // Fallback: try simple reload after a delay
                            setTimeout(() => {{
                                try {{
                                    if (window.location.protocol === 'file:') {{
                                        window.location.reload();
                                    }} else {{
                                        // Fallback: use pathname with default if needed
                                        const pathname = window.location.pathname || '/tankers_map.html';
                                        window.location.href = pathname + '?_=' + Date.now();
                                    }}
                                }} catch (e) {{
                                    console.error('Fallback reload also failed:', e);
                                    resetRefreshButton();
                                }}
                            }}, 1000);
                        }}
                    }}, 500); // Reduced delay for faster response
                }}
                
                // Manual refresh with confirmation
                function manualRefresh() {{
                    console.log('Manual refresh requested');
                    updateStatus('Manual refresh...', '#2196f3');
                    safeReload();
                }}
                
                // Update countdown display
                function updateCountdown() {{
                    if (!isPaused) {{
                        const countdownElement = document.getElementById('countdown');
                        if (countdownElement) {{
                            countdownElement.textContent = countdown;
                        }}
                        
                        if (countdown <= 0) {{
                            // Check if user activity detection is enabled
                            if ({str(PAUSE_ON_USER_ACTIVITY).lower()}) {{
                                if (!userActive) {{
                                    safeReload();
                                }} else {{
                                    console.log('Refresh paused: user is active');
                                    countdown = refreshInterval; // Reset countdown
                                }}
                            }} else {{
                                safeReload();
                            }}
                        }} else {{
                            countdown--;
                        }}
                    }}
                }}
                
                // Toggle auto-refresh pause
                function toggleAutoRefresh() {{
                    isPaused = !isPaused;
                    const pauseBtn = document.getElementById('pause-btn');
                    const timerElement = document.getElementById('refresh-timer');
                    
                    if (isPaused) {{
                        pauseBtn.textContent = 'Resume';
                        pauseBtn.style.background = '#4caf50';
                        timerElement.style.color = '#ff9800';
                        document.getElementById('countdown').textContent = 'PAUSED';
                    }} else {{
                        pauseBtn.textContent = 'Pause';
                        pauseBtn.style.background = '#ff9800';
                        timerElement.style.color = '#2196F3';
                        countdown = refreshInterval; // Reset countdown
                    }}
                }}
                
                // Start countdown timer
                countdownTimer = setInterval(updateCountdown, 1000);
                
                // User activity detection (if enabled)
                if ({str(PAUSE_ON_USER_ACTIVITY).lower()}) {{
                    function resetUserActivity() {{
                        userActive = true;
                        clearTimeout(activityTimeout);
                        activityTimeout = setTimeout(() => {{
                            userActive = false;
                            console.log('User inactive, auto-refresh re-enabled');
                        }}, {USER_ACTIVITY_TIMEOUT * 1000});
                    }}
                    
                    document.addEventListener('mousemove', resetUserActivity);
                    document.addEventListener('click', resetUserActivity);
                    document.addEventListener('scroll', resetUserActivity);
                    document.addEventListener('keypress', resetUserActivity);
                }}
                
                // Keyboard shortcuts
                document.addEventListener('keydown', function(e) {{
                    if (e.key === 'F5' || (e.ctrlKey && e.key === 'r')) {{
                        // Manual refresh - reset countdown
                        countdown = refreshInterval;
                    }}
                    if (e.key === ' ' || e.key === 'Spacebar') {{
                        // Spacebar to toggle pause
                        e.preventDefault();
                        toggleAutoRefresh();
                    }}
                }});
                
                // Page visibility API to pause when tab is not visible
                document.addEventListener('visibilitychange', function() {{
                    if (document.hidden) {{
                        clearInterval(countdownTimer);
                    }} else {{
                        countdownTimer = setInterval(updateCountdown, 1000);
                        countdown = refreshInterval; // Reset when tab becomes visible
                    }}
                }});
                
                // Error handling for failed loads
                window.addEventListener('error', function(e) {{
                    console.error('Page load error:', e);
                    updateStatus('Error loading page', '#f44336');
                    isRefreshing = false;
                }});
                
                // Detect if page loaded successfully
                window.addEventListener('load', function() {{
                    console.log('Page loaded successfully');
                    updateStatus('Ready', '#4caf50');
                    isRefreshing = false;
                }});
                
                // DOM content loaded handler
                document.addEventListener('DOMContentLoaded', function() {{
                    updateStatus('Page ready', '#4caf50');
                    isRefreshing = false;
                }});
                
                // Fallback error recovery with retry mechanism
                let refreshAttempts = 0;
                const maxRefreshAttempts = 3;
                
                function handleRefreshFailure() {{
                    refreshAttempts++;
                    console.warn(`Refresh attempt ${{refreshAttempts}} failed`);
                    
                    if (refreshAttempts < maxRefreshAttempts) {{
                        updateStatus(`Retry ${{refreshAttempts}}/${{maxRefreshAttempts}}`, '#ff9800');
                        setTimeout(() => {{
                            console.log('Retrying with simple reload...');
                            window.location.reload(true);
                        }}, 2000 * refreshAttempts); // Progressive delay
                    }} else {{
                        updateStatus('Refresh failed - manual action needed', '#f44336');
                        isRefreshing = false;
                        
                        // Re-enable controls
                        const refreshBtn = document.getElementById('refresh-btn');
                        if (refreshBtn) {{
                            refreshBtn.disabled = false;
                            refreshBtn.textContent = 'Try Again';
                            refreshBtn.style.background = '#f44336';
                        }}
                    }}
                }}
                
                // Timeout handler
                setTimeout(() => {{
                    if (isRefreshing) {{
                        console.log('Refresh timeout, attempting recovery...');
                        handleRefreshFailure();
                    }}
                }}, 15000); // 15 second timeout
                
                console.log('Auto-refresh enabled: {refresh_interval}s interval with safe reload');
            </script>
            '''
            title_html += script_html
        
        return title_html

    def open_map(self):
        """Open the map in the default web browser."""
        map_path = os.path.abspath(self.output_file)
        webbrowser.open(f'file://{map_path}')
        logger.info(f"🌐 Map opened in browser")
        if ENABLE_AUTO_REFRESH:
            logger.info(f"   Auto-refresh: {HTML_AUTO_REFRESH_SECONDS}s (Spacebar to pause, F5 to refresh)")
        logger.info("")
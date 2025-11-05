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
                   SHIP_TYPE_NAMES, TANKER_TYPES)
from models.vessel import Vessel
from models.region import Port

logger = logging.getLogger(__name__)


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
        
    def create_base_map(self) -> folium.Map:
        """
        Create a base Folium map centered on the region.
        
        Returns:
            Folium Map object
        """
        if self.region_name in REGIONS:
            bounds = REGIONS[self.region_name]
            center_lat = (bounds[0][0] + bounds[1][0]) / 2
            center_lon = (bounds[0][1] + bounds[1][1]) / 2
            zoom = MAP_ZOOM_LEVEL
        else:
            center_lat, center_lon = 20, 0
            zoom = 3
        
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
        ship_type_name = SHIP_TYPE_NAMES.get(vessel.ship_type, f"Type {vessel.ship_type}")
        
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
        
        # Different color for tankers vs other vessels
        color = 'darkred' if vessel.is_tanker(TANKER_TYPES) else 'orange'
        
        # Create tooltip with key info
        tooltip_text = f"{vessel.name or vessel.mmsi}"
        if vessel.speed:
            tooltip_text += f" | {vessel.speed} kts"
        if vessel.destination:
            tooltip_text += f" → {vessel.destination}"
        
        folium.CircleMarker(
            [vessel.lat, vessel.lon],
            radius=VESSEL_MARKER_RADIUS,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=tooltip_text,
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.9
        ).add_to(m)
    
    def generate_map(self, vessels: Dict[int, Vessel], auto_open: bool = False):
        """
        Generate complete map with ports and vessels.
        
        Args:
            vessels: Dictionary of vessels keyed by MMSI
            auto_open: Whether to automatically open the map in browser
        """
        active_count = sum(1 for v in vessels.values() if v.has_position())
        tanker_count = sum(1 for v in vessels.values() if v.has_position() and v.is_tanker(TANKER_TYPES))
        
        logger.info(f"\n🗺️  Generating map with {active_count} vessels ({tanker_count} tankers)...")
        
        m = self.create_base_map()
        self.add_ports(m)
        self.add_vessels(m, vessels)
        
        # Add statistics to map title
        title_html = f'''
        <div style="position: fixed; 
                    top: 10px; 
                    left: 50px; 
                    width: 300px; 
                    background-color: white; 
                    border: 2px solid grey; 
                    z-index: 9999; 
                    padding: 10px;
                    border-radius: 5px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.3);">
            <h4 style="margin: 0 0 10px 0;">🛢️ Tankers Tracker</h4>
            <p style="margin: 5px 0; font-size: 12px;"><b>Region:</b> {self.region_name.replace('_', ' ').title()}</p>
            <p style="margin: 5px 0; font-size: 12px;"><b>Active Vessels:</b> {active_count}</p>
            <p style="margin: 5px 0; font-size: 12px;"><b>Tankers:</b> {tanker_count}</p>
            <p style="margin: 5px 0; font-size: 10px; color: gray;">Last updated: {datetime.now().strftime("%H:%M:%S")}</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        m.save(self.output_file)
        logger.info(f"✅ Map saved to {self.output_file}\n")
        
        if auto_open:
            self.open_map()
    
    def open_map(self):
        """Open the map in the default web browser."""
        map_path = os.path.abspath(self.output_file)
        webbrowser.open(f'file://{map_path}')
        logger.info(f"🌐 Map opened in browser\n")
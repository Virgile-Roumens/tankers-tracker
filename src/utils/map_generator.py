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
        
        # Get color based on ship type
        if vessel.ship_type:
            color = vessel.ship_type.get_color()
        else:
            color = '#808080'  # Gray for unknown type
        
        folium.CircleMarker(
            [vessel.lat, vessel.lon],
            radius=VESSEL_MARKER_RADIUS,
            popup=folium.Popup(popup_html, max_width=350),  # Wider for enhanced display
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
        tanker_count = sum(1 for v in vessels.values() if v.has_position() and v.is_tanker())
        
        logger.info(f"\n🗺️  Generating map with {active_count} vessels ({tanker_count} tankers)...")
        
        m = self.create_base_map()
        self.add_ports(m)
        self.add_vessels(m, vessels)
        
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
        
        # No region selector - worldwide mode only
        region_selector_html = ""
        
        # Create controls for auto-refresh
        controls_html = ""
        if ENABLE_AUTO_REFRESH:
            controls_html = f'''
            <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #ddd;">
                <p id="refresh-timer" style="margin: 5px 0; font-size: 10px; color: #2196F3;">
                    Auto-refresh in: <span id="countdown">{refresh_interval}</span>s
                </p>
                <div id="status-indicator" style="font-size: 9px; color: #4caf50; margin: 3px 0;">● Ready</div>
                <button id="pause-btn" onclick="toggleAutoRefresh()" 
                        style="background: #ff9800; color: white; border: none; padding: 2px 6px; 
                               border-radius: 3px; font-size: 10px; cursor: pointer;">
                    Pause
                </button>
                <button id="refresh-btn" onclick="manualRefresh()" 
                        style="background: #4caf50; color: white; border: none; padding: 2px 6px; 
                               border-radius: 3px; font-size: 10px; cursor: pointer; margin-left: 5px;">
                    Refresh Now
                </button>
            </div>
            '''
        
        title_html = f'''
        <div style="position: fixed; 
                    top: 10px; 
                    left: 50px; 
                    width: 320px; 
                    background-color: white; 
                    border: 2px solid grey; 
                    z-index: 9999; 
                    padding: 10px;
                    border-radius: 5px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.3);">
            <h4 style="margin: 0 0 10px 0;">🛢️ Strategic Tanker Tracker</h4>
            {region_selector_html}
            <p style="margin: 5px 0; font-size: 12px;"><b>Active Vessels:</b> {active_count}</p>
            <p style="margin: 5px 0; font-size: 12px;"><b>🛢️ Tankers:</b> <span style="color: darkred; font-weight: bold;">{tanker_count}</span></p>
            <p style="margin: 5px 0; font-size: 10px; color: gray;">Last updated: {datetime.now().strftime("%H:%M:%S")}</p>
            <p style="margin: 5px 0; font-size: 10px; color: gray;">Auto-refresh: {refresh_status}</p>
            {controls_html}
        </div>
        '''
        
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
                    
                    // Create a delay to ensure map generation is complete
                    setTimeout(() => {{
                        try {{
                            // Try cache-busting URL first
                            const currentUrl = window.location.href.split('?')[0].split('#')[0];
                            const timestamp = Date.now();
                            const refreshUrl = currentUrl + '?_=' + timestamp + '&t=' + timestamp;
                            
                            console.log('Cache-busting refresh URL:', refreshUrl);
                            
                            // Test if we can fetch the file first (basic availability check)
                            fetch(refreshUrl, {{ 
                                method: 'GET',
                                cache: 'no-store',
                                headers: {{
                                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                                    'Pragma': 'no-cache',
                                    'Expires': '0'
                                }}
                            }})
                                .then(response => {{
                                    console.log('Fetch response status:', response.status);
                                    if (response.ok) {{
                                        console.log('File available, reloading with cache-bust');
                                        window.location.href = refreshUrl;
                                    }} else {{
                                        console.warn('File returned status ' + response.status);
                                        throw new Error('File not available (status: ' + response.status + ')');
                                    }}
                                }})
                                .catch(error => {{
                                    console.warn('Fetch test failed, using standard reload:', error);
                                    // Try standard reload with cache bust
                                    window.location.href = currentUrl + '?_=' + Date.now();
                                }});
                        }} catch (error) {{
                            console.error('Refresh failed:', error);
                            updateStatus('Refresh failed, retrying...', '#f44336');
                            // Fallback to standard reload
                            setTimeout(() => {{
                                window.location.href = window.location.href.split('?')[0] + '?_=' + Date.now();
                            }}, 1000);
                        }}
                    }}, 1500); // Increased to 1500ms to allow file write completion
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
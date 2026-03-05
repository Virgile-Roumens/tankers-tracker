"""
Web Interface for Tankers Tracker

A lightweight HTTP server that provides a web interface for switching regions
and managing the tanker tracker.
"""

import asyncio
import json
import os
import sys
import threading
import time
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import parse_qs, urlparse

# Add the src directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import REGIONS

class TrackerManager:
    """Manages the tanker tracker lifecycle."""
    
    def __init__(self):
        self.tracker = None
        self.tracker_thread: Optional[threading.Thread] = None
        self.current_region = None
        self.running = False
    
    def start_tracker(self, region: str) -> bool:
        """Start the tracker for a specific region."""
        try:
            # Stop existing tracker if running
            if self.running:
                self.stop_tracker()
            
            print(f"\n🚀 Starting tracker for region: {region}")
            self.current_region = region
            self.running = True
            
            # Import here to avoid circular imports
            from tankers_tracker import TankersTracker
            
            # Create tracker instance
            self.tracker = TankersTracker(
                selected_region=region,
                max_tracked_ships=5000,
                update_interval=5,
                auto_map_update_seconds=30,
                use_database=True,
                enable_concurrent=True,
                auto_open_browser=False,  # Don't auto-open, web server will handle it
                setup_signal_handlers=False  # Don't setup signal handlers in background thread
            )
            
            # Start tracker in separate thread
            def run_tracker():
                try:
                    self.tracker.start()
                except Exception as e:
                    print(f"❌ Tracker error: {e}")
                    self.running = False
            
            self.tracker_thread = threading.Thread(target=run_tracker, daemon=True)
            self.tracker_thread.start()
            
            # Give it a moment to initialize
            time.sleep(2)
            
            print(f"✅ Tracker started for {region}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start tracker: {e}")
            import traceback
            traceback.print_exc()
            self.running = False
            return False
    
    def stop_tracker(self) -> None:
        """Stop the current tracker."""
        if self.tracker and self.running:
            print(f"\n🛑 Stopping tracker for {self.current_region}...")
            self.running = False
            
            try:
                if hasattr(self.tracker, 'stop'):
                    self.tracker.stop()
            except Exception as e:
                print(f"Warning: Error stopping tracker: {e}")
            
            self.tracker = None
            print("✅ Tracker stopped")
    
    def restart_tracker(self, new_region: str) -> bool:
        """Restart the tracker with a new region."""
        print(f"\n🔄 Restarting tracker: {self.current_region} → {new_region}")
        
        # Give browser time to release the map file before restarting
        # This prevents Windows file locking issues
        time.sleep(1)
        
        return self.start_tracker(new_region)
    
    def get_current_region(self) -> str:
        """Get worldwide region (always)."""
        return 'worldwide'
    
    def set_current_region(self, region: str) -> bool:
        """Set the current region. Returns True on success."""
        if region:
            self.current_region = region
            return True
        return False


# Global tracker manager
tracker_manager = TrackerManager()


class TankersTrackerHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler for the tankers tracker web interface."""
    
    # Class-level region switcher (shared across all requests)
    region_switcher = None
    
    @classmethod
    def set_region_switcher(cls, switcher):
        """Set the shared region switcher instance."""
        cls.region_switcher = switcher
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            # Redirect to the main map
            self.send_response(302)
            self.send_header('Location', '/tankers_map.html')
            self.end_headers()
            return
        
        elif parsed_path.path == '/api/current-region':
            # Return current region as JSON
            self.send_json_response({
                'region': self.region_switcher.get_current_region(),
                'available_regions': list(REGIONS.keys())
            })
            return
        
        elif parsed_path.path == '/api/regions':
            # Return all available regions
            regions_info = {}
            for region_code, bounds in REGIONS.items():
                regions_info[region_code] = {
                    'name': self._get_region_display_name(region_code),
                    'bounds': bounds
                }
            
            self.send_json_response(regions_info)
            return
        
        elif parsed_path.path == '/api/vessels':
            # Return vessel data with optional filtering
            self._handle_vessels_api(parsed_path)
            return
        
        elif parsed_path.path == '/api/vessels/bulk-carriers':
            # Return bulk carrier data with optional class filtering
            self._handle_bulk_carriers_api(parsed_path)
            return
        
        elif parsed_path.path == '/api/vessels/tankers':
            # Return tanker data
            self._handle_tankers_api(parsed_path)
            return
        
        elif parsed_path.path == '/api/statistics':
            # Return classification statistics
            self._handle_statistics_api()
            return
        
        elif parsed_path.path == '/api/filters':
            # Return available filter options
            self._handle_filters_api()
            return
        
        # Handle static files normally
        return super().do_GET()
    
    def _handle_vessels_api(self, parsed_path):
        """Handle /api/vessels endpoint with optional filters."""
        try:
            from services.bulk_tracking_service import classify_all_vessels, get_bulk_carriers, get_tankers
            from enums.bulk_carrier_class import BulkCarrierClass
            from enums.tanker_class import TankerClass
            
            query_params = parse_qs(urlparse(self.path).query)
            category = query_params.get('category', [None])[0]
            bulk_class = query_params.get('bulk_class', [None])[0]
            tanker_class = query_params.get('tanker_class', [None])[0]
            
            # Get vessels from tracker
            vessels = {}
            if tracker_manager.tracker and hasattr(tracker_manager.tracker, 'vessel_service'):
                vessels = tracker_manager.tracker.vessel_service.get_active_vessels()
                classify_all_vessels(vessels)
            
            # Apply filters
            if category:
                vessels = {k: v for k, v in vessels.items()
                          if getattr(v, 'vessel_category', None) == category}
            
            if bulk_class:
                bc = BulkCarrierClass.from_string(bulk_class)
                if bc:
                    vessels = {k: v for k, v in vessels.items()
                              if getattr(v, 'bulk_carrier_class', None) == bc}
            
            if tanker_class:
                tc = TankerClass.from_string(tanker_class)
                if tc:
                    vessels = {k: v for k, v in vessels.items()
                              if getattr(v, 'tanker_class', None) == tc}
            
            self.send_json_response({
                'count': len(vessels),
                'vessels': [v.to_dict() for v in vessels.values()]
            })
        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)
    
    def _handle_bulk_carriers_api(self, parsed_path):
        """Handle /api/vessels/bulk-carriers endpoint."""
        try:
            from services.bulk_tracking_service import classify_all_vessels, get_bulk_carriers, get_bulk_carriers_by_class
            from enums.bulk_carrier_class import BulkCarrierClass
            
            query_params = parse_qs(urlparse(self.path).query)
            bulk_class_str = query_params.get('class', [None])[0]
            
            vessels = {}
            if tracker_manager.tracker and hasattr(tracker_manager.tracker, 'vessel_service'):
                vessels = tracker_manager.tracker.vessel_service.get_active_vessels()
                classify_all_vessels(vessels)
            
            if bulk_class_str:
                bc = BulkCarrierClass.from_string(bulk_class_str)
                if bc:
                    vessels = get_bulk_carriers_by_class(vessels, bc)
                else:
                    self.send_json_response({
                        'error': f'Invalid bulk class: {bulk_class_str}',
                        'valid_classes': [c.value for c in BulkCarrierClass]
                    }, status=400)
                    return
            else:
                vessels = get_bulk_carriers(vessels)
            
            self.send_json_response({
                'count': len(vessels),
                'vessels': [v.to_dict() for v in vessels.values()],
                'available_classes': [
                    {'name': c.value, 'display_name': c.display_name, 'dwt_range': c.dwt_range_str}
                    for c in BulkCarrierClass
                ]
            })
        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)
    
    def _handle_tankers_api(self, parsed_path):
        """Handle /api/vessels/tankers endpoint."""
        try:
            from services.bulk_tracking_service import classify_all_vessels, get_tankers
            
            vessels = {}
            if tracker_manager.tracker and hasattr(tracker_manager.tracker, 'vessel_service'):
                vessels = tracker_manager.tracker.vessel_service.get_active_vessels()
                classify_all_vessels(vessels)
            
            tankers = get_tankers(vessels)
            self.send_json_response({
                'count': len(tankers),
                'vessels': [v.to_dict() for v in tankers.values()]
            })
        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)
    
    def _handle_statistics_api(self):
        """Handle /api/statistics endpoint."""
        try:
            from services.bulk_tracking_service import classify_all_vessels
            
            vessels = {}
            if tracker_manager.tracker and hasattr(tracker_manager.tracker, 'vessel_service'):
                vessels = tracker_manager.tracker.vessel_service.get_active_vessels()
            
            stats = classify_all_vessels(vessels)
            self.send_json_response(stats)
        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)
    
    def _handle_filters_api(self):
        """Handle /api/filters endpoint - list available filter options."""
        try:
            from enums.bulk_carrier_class import BulkCarrierClass
            from enums.tanker_class import TankerClass
            
            self.send_json_response({
                'categories': ['Tanker', 'Bulk Carrier', 'Cargo', 'Other'],
                'bulk_carrier_classes': [
                    {
                        'value': c.value,
                        'display_name': c.display_name,
                        'dwt_range': c.dwt_range_str,
                        'typical_cargo': c.typical_cargo,
                        'color': c.color
                    }
                    for c in BulkCarrierClass
                ],
                'tanker_classes': [
                    {
                        'value': c.value,
                        'display_name': c.display_name
                    }
                    for c in TankerClass
                ]
            })
        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)
    
    def do_POST(self):
        """Handle POST requests (no endpoints - worldwide only)."""
        # No POST endpoints - worldwide mode only
        self.send_response(405)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Method Not Allowed')
    
    def send_json_response(self, data: Dict[str, Any], status: int = 200):
        """Send a JSON response."""
        json_data = json.dumps(data, indent=2).encode('utf-8')
        
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(json_data)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        self.wfile.write(json_data)
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _get_region_display_name(self, region_code: str) -> str:
        """Get a user-friendly display name for a region."""
        region_names = {
            'persian_gulf': '🛢️ Persian Gulf',
            'singapore_strait': '🇸🇬 Singapore Strait',
            'suez_canal': '🇪🇬 Suez Canal',
            'us_gulf': '🇺🇸 US Gulf',
            'north_sea': '🌊 North Sea',
            'mediterranean': '🏖️ Mediterranean',
            'malacca': '🚢 Malacca Strait',
            'gibraltar': '🏔️ Gibraltar',
            'panama': '🇵🇦 Panama Canal'
        }
        return region_names.get(region_code, region_code.replace('_', ' ').title())
    
    def log_message(self, format, *args):
        """Override to reduce logging noise."""
        # Only log important requests
        if '/api/' in self.path or self.command == 'POST':
            super().log_message(format, *args)


class TankersWebServer:
    """Web server for the tankers tracker interface."""
    
    def __init__(self, port: int = 8000, host: str = 'localhost'):
        """Initialize the web server."""
        self.port = port
        self.host = host
        self.server = None
        self.server_thread = None
        
        # Use the global tracker manager as the region switcher
        TankersTrackerHandler.set_region_switcher(tracker_manager)
    
    def start(self, auto_open: bool = True) -> None:
        """Start the web server and tracker."""
        try:
            # Change to the src directory to serve static files
            os.chdir(Path(__file__).parent)
            
            # Get initial region
            initial_region = tracker_manager.get_current_region()
            
            print(f"\n🌐 Starting Tankers Tracker Web Server")
            print(f"📍 Server URL: http://{self.host}:{self.port}")
            print(f"📋 Map URL: http://{self.host}:{self.port}/tankers_map.html")
            print(f"🔧 API URL: http://{self.host}:{self.port}/api/")
            print("=" * 60)
            
            # Start the tracker first
            print(f"\n📡 Starting AIS tracker for region: {initial_region}")
            tracker_manager.start_tracker(initial_region)
            
            # Create and start the HTTP server
            self.server = HTTPServer((self.host, self.port), TankersTrackerHandler)
            
            # Start server in a separate thread
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            
            if auto_open:
                time.sleep(3)  # Give tracker/server time to start
                webbrowser.open(f"http://{self.host}:{self.port}/tankers_map.html")
            
            print("\n✅ Server started successfully!")
            print("💡 Use the dropdown in the map to switch regions")
            print("💡 Press Ctrl+C to stop the server\n")
            
            # Keep the main thread alive
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop()
                
        except OSError as e:
            if e.errno == 48 or 'address already in use' in str(e).lower():
                print(f"❌ Port {self.port} is already in use. Try a different port.")
            else:
                print(f"❌ Failed to start server: {e}")
        except Exception as e:
            print(f"❌ Server error: {e}")
            import traceback
            traceback.print_exc()
    
    def stop(self) -> None:
        """Stop the web server and tracker."""
        print("\n🛑 Shutting down...")
        
        # Stop tracker
        tracker_manager.stop_tracker()
        
        # Stop server
        if self.server:
            print("Stopping web server...")
            self.server.shutdown()
            self.server.server_close()
            
            if self.server_thread:
                self.server_thread.join(timeout=2)
            
            print("✅ Server stopped")


def main():
    """Main entry point for the web server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Tankers Tracker Web Interface")
    parser.add_argument('--port', '-p', type=int, default=8000,
                       help='Port to run the server on (default: 8000)')
    parser.add_argument('--host', default='localhost',
                       help='Host to bind the server to (default: localhost)')
    parser.add_argument('--no-browser', action='store_true',
                       help='Do not auto-open browser')
    
    args = parser.parse_args()
    
    try:
        server = TankersWebServer(port=args.port, host=args.host)
        server.start(auto_open=not args.no_browser)
    except Exception as e:
        print(f"❌ Failed to start web interface: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
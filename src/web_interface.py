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
                max_tracked_ships=1000,
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
        """Get the current region. Returns default if not set."""
        return self.current_region or 'persian_gulf'
    
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
        
        # Handle static files normally
        return super().do_GET()
    
    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/change-region':
            try:
                # Read POST data
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                
                # Parse JSON data
                try:
                    data = json.loads(post_data)
                    new_region = data.get('region')
                except json.JSONDecodeError:
                    # Try form data
                    form_data = parse_qs(post_data)
                    new_region = form_data.get('region', [None])[0]
                
                if not new_region:
                    self.send_json_response({'error': 'No region specified'}, status=400)
                    return
                
                if new_region not in REGIONS:
                    self.send_json_response({
                        'error': f'Invalid region: {new_region}',
                        'available_regions': list(REGIONS.keys())
                    }, status=400)
                    return
                
                # Switch region in region switcher (saves preference)
                success = self.region_switcher.set_current_region(new_region)
                
                if success:
                    # Restart tracker with new region
                    tracker_started = tracker_manager.restart_tracker(new_region)
                    
                    self.send_json_response({
                        'success': True,
                        'region': new_region,
                        'tracker_restarted': tracker_started,
                        'message': f'Region switched to {new_region}. Tracker is restarting...'
                    })
                else:
                    self.send_json_response({
                        'error': 'Failed to switch region'
                    }, status=500)
                
            except Exception as e:
                self.send_json_response({
                    'error': f'Server error: {str(e)}'
                }, status=500)
            
            return
        
        # Method not allowed for other paths
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
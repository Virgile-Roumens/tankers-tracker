"""
Enhanced Live Tanker Tracker Application

A high-performance, real-time vessel tracking system for monitoring tankers
and cargo ships using AIS (Automatic Identification System) data.

Features:
- Real-time AIS data streaming with concurrent processing
- SQLite database for persistent vessel storage
- Enhanced vessel information (25+ fields per vessel)
- Interactive Folium maps with comprehensive vessel details
- Configurable regional tracking with multiple predefined regions
- Automatic map updates and background processing
- Production-ready architecture with service layers

Author: Enhanced Tankers Tracker
Version: 2.0
Date: 2025
"""

import asyncio
import logging
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Dict, Optional

from config import (
    AUTO_MAP_UPDATE_SECONDS, 
    DATABASE_PATH, 
    ENABLE_CONCURRENT_PROCESSING,
    LOG_LEVEL, 
    MAX_TRACKED_SHIPS, 
    MESSAGE_BATCH_SIZE,
    REGIONS, 
    UPDATE_INTERVAL,
    USE_DATABASE_CACHE
)
from models.vessel import Vessel
from utils.ais_client import AISClient
from utils.map_generator import MapGenerator
from utils.vessel_info_service import VesselInfoService

# Configure logging with better formatting
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('TankersTracker')


class TankersTracker:
    """
    Enhanced Live Tanker Tracker Application
    
    A production-ready vessel tracking system with the following capabilities:
    
    Performance Features:
    - Track up to 500+ vessels simultaneously (configurable)
    - Concurrent message processing for high throughput
    - SQLite database caching for persistence
    - Smart map update strategies to prevent overload
    
    Data Features:
    - 25+ vessel attributes (position, dimensions, voyage, etc.)
    - Real-time AIS data from multiple vessel types
    - Historical vessel tracking across sessions
    - Comprehensive vessel information display
    
    Regional Support:
    - Persian Gulf, Mediterranean, North Sea, Singapore Strait
    - Suez Canal, US Gulf, Panama Canal, Gibraltar
    - Custom bounding box support
    - Major ports and terminals display
    """
    
    def __init__(self, 
                 selected_region: str = "mediterranean",
                 max_tracked_ships: int = MAX_TRACKED_SHIPS,
                 update_interval: int = UPDATE_INTERVAL,
                 auto_map_update_seconds: int = AUTO_MAP_UPDATE_SECONDS,
                 use_database: bool = USE_DATABASE_CACHE,
                 enable_concurrent: bool = ENABLE_CONCURRENT_PROCESSING,
                 batch_size: int = MESSAGE_BATCH_SIZE,
                 auto_open_browser: bool = False,
                 setup_signal_handlers: bool = True):
        """
        Initialize Enhanced Tanker Tracker
        
        Args:
            selected_region: Region to track ('mediterranean', 'persian_gulf', etc.)
            max_tracked_ships: Maximum vessels to track simultaneously
            update_interval: Update map every N position reports
            auto_map_update_seconds: Background map refresh interval (seconds)
            use_database: Enable SQLite database for persistence
            enable_concurrent: Enable concurrent message processing
            batch_size: Messages to process per batch (concurrent mode)
            auto_open_browser: Auto-open map in browser on initial generation
            setup_signal_handlers: Setup Ctrl+C handlers (only works in main thread)
        """
        # Configuration
        self.selected_region = selected_region
        self.max_tracked_ships = max_tracked_ships
        self.update_interval = update_interval
        self.auto_map_update_seconds = auto_map_update_seconds
        self.use_database = use_database
        self.enable_concurrent = enable_concurrent
        self.batch_size = batch_size
        self.auto_open_browser = auto_open_browser
        
        # Validate and set region bounds
        self._setup_region()
        
        # Initialize core components
        self._initialize_components()
        
        # Tracking state
        self.running = False
        self.position_update_count = 0
        self.last_map_update = time.time()
        
        # Background thread handle
        self.auto_updater_thread: Optional[threading.Thread] = None
        
        # Setup graceful shutdown only if in main thread
        if setup_signal_handlers:
            self._setup_signal_handlers()
    
    def _setup_region(self) -> None:
        """Validate region and set bounding box coordinates."""
        if self.selected_region not in REGIONS:
            logger.warning(f"Region '{self.selected_region}' not found in config")
            logger.info("Available regions: " + ", ".join(REGIONS.keys()))
            logger.info("Falling back to worldwide tracking")
            self.region_bounds = [[-90, -180], [90, 180]]
        else:
            self.region_bounds = REGIONS[self.selected_region]
            logger.info(f"Region '{self.selected_region}' validated")
    
    def _initialize_components(self) -> None:
        """Initialize core application components."""
        try:
            # Map generator for visualization
            self.map_generator = MapGenerator(
                region_name=self.selected_region,
                output_file="tankers_map.html"
            )
            
            # Vessel service for data management
            self.vessel_service = VesselInfoService(
                use_database=self.use_database,
                db_path=DATABASE_PATH
            )
            
            # AIS client will be initialized on start
            self.ais_client: Optional[AISClient] = None
            
            logger.info("Core components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    def _setup_signal_handlers(self) -> None:
        """Setup graceful shutdown on Ctrl+C."""
        def signal_handler(signum, frame):
            logger.info("Shutdown signal received")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
    
    def _is_vessel_in_region(self, vessel: Vessel) -> bool:
        """
        Check if a vessel is within the current region bounds.
        
        Args:
            vessel: Vessel to check
            
        Returns:
            True if vessel is in region, False otherwise
        """
        if not vessel.has_position():
            return False
        
        # Region bounds: [[south, west], [north, east]]
        south, west = self.region_bounds[0]
        north, east = self.region_bounds[1]
        
        # Check if vessel is within bounds
        in_latitude = south <= vessel.lat <= north
        in_longitude = west <= vessel.lon <= east
        
        return in_latitude and in_longitude
    
    def _get_vessels_in_region(self, expand_margin: float = 0.0) -> Dict[int, Vessel]:
        """
        Get only vessels that are currently in the tracked region.
        
        Args:
            expand_margin: Degrees to expand the search area (for better coverage)
        
        Returns:
            Dictionary of vessels in region
        """
        all_vessels = self.vessel_service.get_active_vessels()
        
        # Region bounds: [[south, west], [north, east]]
        south, west = self.region_bounds[0]
        north, east = self.region_bounds[1]
        
        # Expand bounds if requested
        south -= expand_margin
        north += expand_margin
        west -= expand_margin
        east += expand_margin
        
        vessels_in_region = {}
        for mmsi, vessel in all_vessels.items():
            if not vessel.has_position():
                continue
                
            # Check if vessel is within bounds
            in_latitude = south <= vessel.lat <= north
            in_longitude = west <= vessel.lon <= east
            
            if in_latitude and in_longitude:
                vessels_in_region[mmsi] = vessel
        
        return vessels_in_region
        
    def _on_static_data(self, vessel: Vessel):
        """Callback for when vessel static data is received."""
        # Update vessel in service (handles caching and database)
        self.vessel_service.update_vessel(vessel)
    
    def _on_position_update(self, vessel: Vessel):
        """Callback for when vessel position is updated."""
        # Update vessel in service
        self.vessel_service.update_vessel(vessel)
        
        self.position_update_count += 1
        
        # Update map periodically based on position count
        if self.position_update_count % self.update_interval == 0:
            self._update_map()
    
    def _update_map(self):
        """Update the map with current vessel positions (vessels in/near region)."""
        vessels = self._get_vessels_in_region(expand_margin=0.5)  # Slightly expanded for updates
        if len(vessels) > 0:
            self.map_generator.generate_map(vessels, auto_open=False)
            self.last_map_update = time.time()
        else:
            # If still no vessels, just update timestamp
            self.last_map_update = time.time()
    
    def _auto_map_updater(self):
        """Background thread for automatic map updates (worldwide)."""
        while self.running:
            time.sleep(self.auto_map_update_seconds)
            
            # Only update if enough time has passed
            if time.time() - self.last_map_update > self.auto_map_update_seconds:
                # Display all active vessels worldwide
                vessels = self.vessel_service.get_active_vessels()
                
                if len(vessels) > 0:
                    logger.info("[AUTO-UPDATE] Refreshing map...")
                    self.map_generator.generate_map(vessels, auto_open=False)
                self.last_map_update = time.time()
    
    async def _run_ais_connection(self) -> None:
        """Run the AIS client connection with error handling."""
        try:
            self.ais_client = AISClient(
                region_bounds=self.region_bounds,
                max_vessels=self.max_tracked_ships,
                on_static_data=self._on_static_data,
                on_position_update=self._on_position_update,
                batch_size=self.batch_size,
                enable_concurrent_processing=self.enable_concurrent
            )
            await self.ais_client.connect()
        except Exception as e:
            logger.error(f"AIS connection error: {e}")
            raise
    
    def start(self) -> None:
        """Start the tanker tracker application."""
        try:
            self._display_startup_banner()
            self.running = True
            self._load_cached_vessels()
            self._create_initial_map()
            self._start_background_services()
            
            logger.info("Starting AIS connection...\n")
            asyncio.run(self._run_ais_connection())
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
        except Exception as e:
            logger.error(f"Application startup failed: {e}")
            raise
        finally:
            self.stop()
    
    def _display_startup_banner(self) -> None:
        """Display startup information and configuration."""
        banner = f"""
{'=' * 75}
🛢️  TANKER TRACKER v2.0 - WORLDWIDE MODE
{'=' * 75}
Configuration:
  Mode: 🌍 WORLDWIDE (All 30 regions)
  Max vessels: {self.max_tracked_ships:,}
  Update interval: Every {self.update_interval} positions
  Auto-refresh: Every {self.auto_map_update_seconds} seconds
  Database caching: {'✅ Enabled' if self.use_database else '❌ Disabled'}
  Concurrent processing: {'✅ Enabled' if self.enable_concurrent else '❌ Disabled'}

Worldwide bounds: [-90, -180] to [90, 180]
{'=' * 75}
"""
        print(banner)
    
    def _load_cached_vessels(self) -> None:
        """Load previously cached vessels from database."""
        try:
            cached_vessels = self.vessel_service.get_all_vessels()
            if len(cached_vessels) > 0:
                active_count = len([v for v in cached_vessels.values() if v.has_position()])
                in_region_count = len(self._get_vessels_in_region())
                logger.info(f"📚 Loaded {len(cached_vessels):,} vessels from cache ({active_count:,} active, {in_region_count:,} in current region)")
            else:
                logger.info("No cached vessels found - starting fresh")
        except Exception as e:
            logger.warning(f"Failed to load cached vessels: {e}")
    
    def _create_initial_map(self) -> None:
        """Create and display initial worldwide map."""
        try:
            logger.info("Creating initial map...")
            
            # Display all vessels worldwide
            vessels_to_display = self.vessel_service.get_active_vessels()
            
            self.map_generator.generate_map(vessels_to_display, auto_open=self.auto_open_browser)
            
            if len(vessels_to_display) > 0:
                logger.info(f"Initial map created with {len(vessels_to_display):,} worldwide vessels")
            else:
                logger.info("Initial map created - waiting for AIS data...")
        except Exception as e:
            logger.error(f"Failed to create initial map: {e}")
    
    def _start_background_services(self) -> None:
        """Start background threads for map updates."""
        try:
            logger.info("Starting background map updater...")
            self.auto_updater_thread = threading.Thread(
                target=self._auto_map_updater,
                name="MapUpdater",
                daemon=True
            )
            self.auto_updater_thread.start()
        except Exception as e:
            logger.error(f"Failed to start background services: {e}")
    
    def stop(self) -> None:
        """Stop the tanker tracker and cleanup resources."""
        if not self.running:
            return
            
        logger.info("🛑 Stopping tanker tracker...")
        self.running = False
        
        # Stop AIS client first
        if self.ais_client and hasattr(self.ais_client, 'stop'):
            self.ais_client.stop()
        
        try:
            final_stats = self.vessel_service.get_statistics()
            self._generate_final_map()
            self._display_final_statistics(final_stats)
            self._cleanup_resources()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        logger.info("✅ Tanker tracker stopped successfully")
    
    def _generate_final_map(self) -> None:
        """Generate final map with vessels in current region."""
        try:
            vessels_in_region = self._get_vessels_in_region()
            if len(vessels_in_region) > 0:
                logger.info(f"Generating final map with {len(vessels_in_region):,} vessels in region...")
                self.map_generator.generate_map(vessels_in_region, auto_open=False)
        except Exception as e:
            logger.error(f"Failed to generate final map: {e}")
    
    def _display_final_statistics(self, stats: Dict) -> None:
        """Display comprehensive final statistics."""
        try:
            print(f"\n{'=' * 75}")
            print("📊 FINAL STATISTICS")
            print(f"{'=' * 75}")
            print(f"Session Summary:")
            print(f"  Total vessels tracked: {stats.get('total_vessels', 0):,}")
            print(f"  Active vessels: {stats.get('active_vessels', 0):,}")
            print(f"  Position updates processed: {self.position_update_count:,}")
            
            if 'database' in stats and stats['database']:
                db_stats = stats['database']
                print(f"\nDatabase Summary:")
                print(f"  Total in database: {db_stats.get('total_vessels', 0):,}")
                print(f"  Tankers: {db_stats.get('tankers', 0):,}")
                print(f"  Vessels with positions: {db_stats.get('with_position', 0):,}")
            
            print(f"{'=' * 75}")
        except Exception as e:
            logger.error(f"Error displaying statistics: {e}")
    
    def _cleanup_resources(self) -> None:
        """Cleanup application resources."""
        try:
            if hasattr(self, 'vessel_service'):
                self.vessel_service.close()
            
            if self.auto_updater_thread and self.auto_updater_thread.is_alive():
                self.auto_updater_thread.join(timeout=2.0)
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def main():
    """Main entry point for the Enhanced Tanker Tracker application."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Live Tanker Tracker")
    parser.add_argument('--region', '-r', default=None, 
                       help='Region to track (default: uses saved preference or suez_canal)')
    parser.add_argument('--max-ships', type=int, default=10000,
                       help='Maximum ships to track (default: 10000)')
    parser.add_argument('--update-interval', type=int, default=5,
                       help='Map update interval in position reports (default: 5)')
    parser.add_argument('--auto-refresh', type=int, default=15,
                       help='Auto-refresh interval in seconds (default: 15)')
    parser.add_argument('--no-database', action='store_true',
                       help='Disable database caching')
    parser.add_argument('--no-concurrent', action='store_true',
                       help='Disable concurrent processing')
    parser.add_argument('--batch-size', type=int, default=10,
                       help='Message batch size for concurrent processing (default: 10)')
    parser.add_argument('--list-regions', action='store_true',
                       help='List available regions and exit')
    
    args = parser.parse_args()
    
    # List regions if requested
    if args.list_regions:
        print("\n📍 Available Regions:")
        print("=" * 50)
        for region_code, bounds in REGIONS.items():
            print(f"  {region_code:<20} {bounds}")
        print("=" * 50)
        return
    
    # Determine region to use
    selected_region = args.region
    if not selected_region:
        # Try to load from saved preference
        try:
            from pathlib import Path
            import json
            region_file = Path("data/current_region.json")
            if region_file.exists():
                with open(region_file, 'r') as f:
                    data = json.load(f)
                    selected_region = data.get('region', 'suez_canal')
                    logger.info(f"Using saved region preference: {selected_region}")
            else:
                selected_region = 'suez_canal'
                logger.info(f"No saved preference found, using default: {selected_region}")
        except Exception as e:
            selected_region = 'suez_canal'
            logger.warning(f"Failed to load region preference: {e}")
            logger.info(f"Using default region: {selected_region}")
    
    # Validate region
    if selected_region not in REGIONS:
        logger.error(f"Invalid region: {selected_region}")
        logger.info(f"Available regions: {', '.join(REGIONS.keys())}")
        sys.exit(1)
    
    try:
        tracker = TankersTracker(
            selected_region=selected_region,
            max_tracked_ships=args.max_ships,
            update_interval=args.update_interval,
            auto_map_update_seconds=args.auto_refresh,
            use_database=not args.no_database,
            enable_concurrent=not args.no_concurrent,
            batch_size=args.batch_size,
            auto_open_browser=True  # Auto-open for standalone usage
        )
        
        tracker.start()
        
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

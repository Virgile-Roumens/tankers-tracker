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
                 batch_size: int = MESSAGE_BATCH_SIZE):
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
        """
        # Configuration
        self.selected_region = selected_region
        self.max_tracked_ships = max_tracked_ships
        self.update_interval = update_interval
        self.auto_map_update_seconds = auto_map_update_seconds
        self.use_database = use_database
        self.enable_concurrent = enable_concurrent
        self.batch_size = batch_size
        
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
        
        # Setup graceful shutdown
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
        """Update the map with current vessel positions."""
        vessels = self.vessel_service.get_active_vessels()
        if len(vessels) > 0:
            self.map_generator.generate_map(vessels, auto_open=False)
            self.last_map_update = time.time()
    
    def _auto_map_updater(self):
        """Background thread for automatic map updates."""
        while self.running:
            time.sleep(self.auto_map_update_seconds)
            
            # Only update if enough time has passed
            if time.time() - self.last_map_update > self.auto_map_update_seconds:
                vessels = self.vessel_service.get_active_vessels()
                if len(vessels) > 0:
                    logger.info("[AUTO-UPDATE] Refreshing map...")
                    self.map_generator.generate_map(vessels, auto_open=False)
                    self.last_map_update = time.time()
    
    async def _run_ais_client(self):
        """Run the AIS client connection."""
        self.ais_client = AISClient(
            region_bounds=self.region_bounds,
            max_vessels=self.max_tracked_ships,
            on_static_data=self._on_static_data,
            on_position_update=self._on_position_update,
            batch_size=MESSAGE_BATCH_SIZE,
            enable_concurrent_processing=self.enable_concurrent
        )
        
        await self.ais_client.connect()
    
    def start(self):
        """Start the tanker tracker application."""
        self.running = True
        
        print("=" * 70)
        print("🛢️  ENHANCED LIVE TANKER TRACKER")
        print("=" * 70)
        print(f"Region: {self.selected_region.upper()}")
        print(f"Max vessels: {self.max_tracked_ships}")
        print(f"Update interval: Every {self.update_interval} positions")
        print(f"Auto-refresh: Every {self.auto_map_update_seconds} seconds")
        print(f"Database caching: {'Enabled' if self.use_database else 'Disabled'}")
        print(f"Concurrent processing: {'Enabled' if self.enable_concurrent else 'Disabled'}")
        print("=" * 70 + "\n")
        
        # Show cached vessels if any
        cached = self.vessel_service.get_all_vessels()
        if len(cached) > 0:
            logger.info(f"📚 Loaded {len(cached)} vessels from cache")
        
        # Create initial map
        logger.info("Creating initial map...")
        vessels = self.vessel_service.get_active_vessels()
        self.map_generator.generate_map(vessels, auto_open=True)
        
        # Start background auto-updater thread
        logger.info("Starting auto-updater thread...")
        updater_thread = threading.Thread(target=self._auto_map_updater, daemon=True)
        updater_thread.start()
        
        # Start AIS client
        try:
            logger.info("Starting AIS client...\n")
            asyncio.run(self._run_ais_client())
            
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the tanker tracker application."""
        logger.info("\n⏹️  Stopping tracker...")
        self.running = False
        
        # Get final statistics
        stats = self.vessel_service.get_statistics()
        
        # Final map update
        vessels = self.vessel_service.get_active_vessels()
        self.map_generator.generate_map(vessels, auto_open=False)
        
        # Display statistics
        print("\n" + "=" * 70)
        print("📊 FINAL STATISTICS")
        print("=" * 70)
        print(f"Total vessels tracked: {stats.get('total_vessels', 0)}")
        print(f"Active vessels: {stats.get('active_vessels', 0)}")
        if 'database' in stats:
            db_stats = stats['database']
            print(f"Tankers in database: {db_stats.get('tankers', 0)}")
            print(f"Vessels with position: {db_stats.get('with_position', 0)}")
        print("=" * 70)
        
        # Close vessel service (saves to database)
        self.vessel_service.close()
        
        logger.info("Tracker stopped")


    
    # =========================================================================
    # AIS Data Callbacks
    # =========================================================================
    
    def _on_vessel_static_data(self, vessel: Vessel) -> None:
        """Handle vessel static data updates (name, dimensions, etc.)."""
        try:
            enriched_vessel = self.vessel_service.enrich_vessel_data(vessel)
            self.vessel_service.update_vessel(enriched_vessel)
        except Exception as e:
            logger.error(f"Error processing static data for vessel {vessel.mmsi}: {e}")
    
    def _on_vessel_position_update(self, vessel: Vessel) -> None:
        """Handle vessel position updates (GPS, speed, course, etc.)."""
        try:
            self.vessel_service.update_vessel(vessel)
            self.position_update_count += 1
            
            if self.position_update_count % self.update_interval == 0:
                self._trigger_map_update()
        except Exception as e:
            logger.error(f"Error processing position update for vessel {vessel.mmsi}: {e}")
    
    def _trigger_map_update(self) -> None:
        """Trigger immediate map update if vessels are available."""
        try:
            active_vessels = self.vessel_service.get_active_vessels()
            if len(active_vessels) > 0:
                self.map_generator.generate_map(active_vessels, auto_open=False)
                self.last_map_update = time.time()
        except Exception as e:
            logger.error(f"Error updating map: {e}")
    
    def _background_map_updater(self) -> None:
        """Background thread for automatic map updates."""
        logger.info("Background map updater started")
        
        while self.running:
            try:
                time.sleep(self.auto_map_update_seconds)
                time_since_last = time.time() - self.last_map_update
                
                if time_since_last >= self.auto_map_update_seconds:
                    active_vessels = self.vessel_service.get_active_vessels()
                    if len(active_vessels) > 0:
                        logger.info(f"[AUTO-UPDATE] Refreshing map with {len(active_vessels)} vessels")
                        self.map_generator.generate_map(active_vessels, auto_open=False)
                        self.last_map_update = time.time()
            except Exception as e:
                if self.running:
                    logger.error(f"Background updater error: {e}")
                break
    
    async def _run_ais_connection(self) -> None:
        """Run the AIS client connection with error handling."""
        try:
            self.ais_client = AISClient(
                region_bounds=self.region_bounds,
                max_vessels=self.max_tracked_ships,
                on_static_data=self._on_vessel_static_data,
                on_position_update=self._on_vessel_position_update,
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
🛢️  ENHANCED LIVE TANKER TRACKER v2.0
{'=' * 75}
Configuration:
  Region: {self.selected_region.upper().replace('_', ' ')}
  Max vessels: {self.max_tracked_ships:,}
  Update interval: Every {self.update_interval} positions
  Auto-refresh: Every {self.auto_map_update_seconds} seconds
  Database caching: {'✅ Enabled' if self.use_database else '❌ Disabled'}
  Concurrent processing: {'✅ Enabled' if self.enable_concurrent else '❌ Disabled'}
  
Region bounds: {self.region_bounds}
{'=' * 75}
"""
        print(banner)
    
    def _load_cached_vessels(self) -> None:
        """Load previously cached vessels from database."""
        try:
            cached_vessels = self.vessel_service.get_all_vessels()
            if len(cached_vessels) > 0:
                active_count = len([v for v in cached_vessels.values() if v.has_position()])
                logger.info(f"📚 Loaded {len(cached_vessels):,} vessels from cache ({active_count:,} active)")
            else:
                logger.info("No cached vessels found - starting fresh")
        except Exception as e:
            logger.warning(f"Failed to load cached vessels: {e}")
    
    def _create_initial_map(self) -> None:
        """Create and display initial map."""
        try:
            logger.info("Creating initial map...")
            active_vessels = self.vessel_service.get_active_vessels()
            self.map_generator.generate_map(active_vessels, auto_open=True)
            
            if len(active_vessels) > 0:
                logger.info(f"Initial map created with {len(active_vessels):,} vessels")
            else:
                logger.info("Initial map created with ports only - vessels will appear as data arrives")
        except Exception as e:
            logger.error(f"Failed to create initial map: {e}")
    
    def _start_background_services(self) -> None:
        """Start background threads for map updates."""
        try:
            logger.info("Starting background map updater...")
            self.auto_updater_thread = threading.Thread(
                target=self._background_map_updater,
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
        
        try:
            final_stats = self.vessel_service.get_statistics()
            self._generate_final_map()
            self._display_final_statistics(final_stats)
            self._cleanup_resources()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        logger.info("✅ Tanker tracker stopped successfully")
    
    def _generate_final_map(self) -> None:
        """Generate final map with all tracked vessels."""
        try:
            active_vessels = self.vessel_service.get_active_vessels()
            if len(active_vessels) > 0:
                logger.info(f"Generating final map with {len(active_vessels):,} vessels...")
                self.map_generator.generate_map(active_vessels, auto_open=False)
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
    try:
        tracker = TankersTracker(
            selected_region="mediterranean",     # Focus region
            max_tracked_ships=500,              # High capacity
            update_interval=5,                  # Balanced updates
            auto_map_update_seconds=15,         # Regular refresh
            use_database=True,                  # Enable persistence
            enable_concurrent=True,             # Enable performance
            batch_size=10                       # Batch processing
        )
        
        tracker.start()
        
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
"""
Main application for Live Tanker Tracker.

This module provides the TankersTracker class which orchestrates
AIS data streaming and map visualization for vessel tracking.
"""

import asyncio
import time
import threading
from datetime import datetime, timezone
from typing import Optional
import logging

from config import (MAX_TRACKED_SHIPS, UPDATE_INTERVAL, AUTO_MAP_UPDATE_SECONDS, 
                   REGIONS, LOG_LEVEL, ENABLE_CONCURRENT_PROCESSING, 
                   MESSAGE_BATCH_SIZE, USE_DATABASE_CACHE, DATABASE_PATH)
from utils.ais_client import AISClient
from utils.map_generator import MapGenerator
from utils.vessel_info_service import VesselInfoService
from models.vessel import Vessel

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class TankersTracker:
    """
    Enhanced tanker tracker with database caching and performance optimization.
    
    Features:
    - Real-time AIS data streaming
    - SQLite database for vessel caching
    - Concurrent message processing
    - Enhanced vessel information display
    - Automatic map updates
    """
    
    def __init__(self, 
                 selected_region: str = "persian_gulf",
                 max_tracked_ships: int = MAX_TRACKED_SHIPS,
                 update_interval: int = UPDATE_INTERVAL,
                 auto_map_update_seconds: int = AUTO_MAP_UPDATE_SECONDS,
                 use_database: bool = USE_DATABASE_CACHE,
                 enable_concurrent: bool = ENABLE_CONCURRENT_PROCESSING):
        """
        Initialize the tanker tracker.
        
        Args:
            selected_region: Name of region to track (from config.REGIONS)
            max_tracked_ships: Maximum number of vessels to track
            update_interval: Update map every N position reports
            auto_map_update_seconds: Auto-update map every N seconds
            use_database: Enable database caching
            enable_concurrent: Enable concurrent message processing
        """
        self.selected_region = selected_region
        self.max_tracked_ships = max_tracked_ships
        self.update_interval = update_interval
        self.auto_map_update_seconds = auto_map_update_seconds
        self.use_database = use_database
        self.enable_concurrent = enable_concurrent
        
        # Validate region
        if selected_region not in REGIONS:
            logger.warning(f"Region '{selected_region}' not found, using worldwide tracking")
            self.region_bounds = [[[-90, -180], [90, 180]]]
        else:
            self.region_bounds = REGIONS[selected_region]
        
        # Initialize components
        self.map_generator = MapGenerator(selected_region)
        self.vessel_service = VesselInfoService(use_database=use_database, db_path=DATABASE_PATH)
        self.ais_client: Optional[AISClient] = None
        
        # Tracking state
        self.position_update_count = 0
        self.last_map_update = time.time()
        self.running = False
        
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


def main():
    """Main entry point for the application."""
    # Enhanced configuration with better defaults
    tracker = TankersTracker(
        selected_region="north_sea",  # Change region here
        max_tracked_ships=500,           # Increased capacity
        update_interval=5,               # Update less frequently for performance
        auto_map_update_seconds=15,      # Auto-refresh interval
        use_database=True,               # Enable database caching
        enable_concurrent=True           # Enable concurrent processing
    )
    
    tracker.start()


if __name__ == "__main__":
    main()


import asyncio
import time
import threading
from datetime import datetime, timezone
from typing import Optional
import logging

from config import (MAX_TRACKED_SHIPS, UPDATE_INTERVAL, AUTO_MAP_UPDATE_SECONDS, 
                   REGIONS, LOG_LEVEL)
from utils.ais_client import AISClient
from utils.map_generator import MapGenerator
from models.vessel import Vessel

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class TankersTracker:
    """
    Main application class for tracking oil tankers and cargo vessels.
    
    Coordinates AIS data streaming, vessel tracking, and map visualization.
    """
    
    def __init__(self, 
                 selected_region,
                 max_tracked_ships: int = MAX_TRACKED_SHIPS,
                 update_interval: int = UPDATE_INTERVAL,
                 auto_map_update_seconds: int = AUTO_MAP_UPDATE_SECONDS):
        """
        Initialize the tanker tracker.
        
        Args:
            selected_region: Name of region to track (from config.REGIONS)
            max_tracked_ships: Maximum number of vessels to track
            update_interval: Update map every N position reports
            auto_map_update_seconds: Auto-update map every N seconds
        """
        self.selected_region = selected_region
        self.max_tracked_ships = max_tracked_ships
        self.update_interval = update_interval
        self.auto_map_update_seconds = auto_map_update_seconds
        
        # Validate region
        if selected_region not in REGIONS:
            logger.warning(f"Region '{selected_region}' not found, using worldwide tracking")
            self.region_bounds = [[[-90, -180], [90, 180]]]
        else:
            self.region_bounds = REGIONS[selected_region]
        
        # Initialize components
        self.map_generator = MapGenerator(selected_region)
        self.ais_client: Optional[AISClient] = None
        
        # Tracking state
        self.position_update_count = 0
        self.last_map_update = time.time()
        self.running = False
        
    def _on_static_data(self, vessel: Vessel):
        """Callback for when vessel static data is received."""
        # Map generator will handle this when generating the map
        pass
    
    def _on_position_update(self, vessel: Vessel):
        """Callback for when vessel position is updated."""
        self.position_update_count += 1
        
        # Update map periodically based on position count
        if self.position_update_count % self.update_interval == 0:
            self._update_map()
    
    def _update_map(self):
        """Update the map with current vessel positions."""
        if self.ais_client:
            vessels = self.ais_client.get_active_vessels()
            self.map_generator.generate_map(vessels, auto_open=False)
            self.last_map_update = time.time()
    
    def _auto_map_updater(self):
        """Background thread for automatic map updates."""
        while self.running:
            time.sleep(self.auto_map_update_seconds)
            
            # Only update if enough time has passed
            if time.time() - self.last_map_update > self.auto_map_update_seconds:
                if self.ais_client:
                    vessels = self.ais_client.get_active_vessels()
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
            on_position_update=self._on_position_update
        )
        
        await self.ais_client.connect()
    
    def start(self):
        """Start the tanker tracker application."""
        self.running = True
        
        print("=" * 70)
        print("🛢️  LIVE TANKER TRACKER")
        print("=" * 70)
        print(f"Region: {self.selected_region.upper()}")
        print(f"Max vessels: {self.max_tracked_ships}")
        print(f"Update interval: Every {self.update_interval} positions")
        print(f"Auto-refresh: Every {self.auto_map_update_seconds} seconds")
        print("=" * 70 + "\n")
        
        # Create initial map with just ports
        logger.info("Creating initial map...")
        self.map_generator.generate_map({}, auto_open=True)
        
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
        
        # Final map update
        if self.ais_client:
            vessels = self.ais_client.get_active_vessels()
            self.map_generator.generate_map(vessels, auto_open=False)
            
            active = len(vessels)
            total = len(self.ais_client.get_vessels())
            logger.info(f"📊 Final stats: {active} active vessels out of {total} tracked")
        
        print("=" * 70)
        logger.info("Tracker stopped")


def main():
    """Main entry point for the application."""
    # Default configuration - customize as needed
    tracker = TankersTracker(
        selected_region="suez_canal",  # Change region here
        max_tracked_ships=100,
        update_interval=2,
        auto_map_update_seconds=10
    )
    
    tracker.start()


if __name__ == "__main__":
    main()
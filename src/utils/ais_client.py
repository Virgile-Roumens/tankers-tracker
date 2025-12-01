"""
AIS Client for connecting to AIS Stream WebSocket and processing vessel data.
"""

import asyncio
import websockets
import json
import time
from datetime import datetime, timezone
from typing import Dict, Callable, Optional, List
import logging
from collections import deque

from config import AIS_API_KEY, AIS_URL
from models.vessel import Vessel
from enums.ship_type import ShipType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AISClient:
    """
    Optimized WebSocket client for AIS Stream service.
    
    Features:
    - Concurrent message processing
    - Message batching for performance
    - Priority queue for tanker data
    - Efficient vessel tracking
    """
    
    def __init__(self, 
                 region_bounds: list,
                 max_vessels: int = 500,
                 on_static_data: Optional[Callable] = None,
                 on_position_update: Optional[Callable] = None,
                 batch_size: int = 10,
                 enable_concurrent_processing: bool = True):
        """
        Initialize AIS client.
        
        Args:
            region_bounds: Bounding box for tracking [[south, west], [north, east]]
            max_vessels: Maximum number of vessels to track (increased default)
            on_static_data: Callback for static data messages
            on_position_update: Callback for position update messages
            batch_size: Number of messages to process in batch
            enable_concurrent_processing: Enable concurrent message processing
        """
        self.region_bounds = region_bounds
        self.max_vessels = max_vessels
        self.on_static_data = on_static_data
        self.on_position_update = on_position_update
        self.batch_size = batch_size
        self.enable_concurrent = enable_concurrent_processing
        
        self.vessels: Dict[int, Vessel] = {}
        self.position_count = 0
        self.static_count = 0
        self.last_summary_time = time.time()
        
        # Message queue for batching
        self.message_queue: deque = deque()
        self.processing_task: Optional[asyncio.Task] = None
        
        # Reconnection parameters
        self.reconnect_attempts = 0
        self.max_reconnect_delay = 60  # Max 60 seconds between reconnects
        self.running = True
        
    async def connect(self):
        """Establish WebSocket connection with automatic reconnection."""
        logger.info("Connecting to AIS Stream...")
        logger.info(f"Tracking region: {self.region_bounds}")
        logger.info(f"Max vessels: {self.max_vessels}")
        logger.info(f"Concurrent processing: {self.enable_concurrent}\n")
        
        while self.running:
            try:
                async with websockets.connect(
                    AIS_URL,
                    ping_interval=20,  # Send ping every 20 seconds
                    ping_timeout=10,   # Wait 10 seconds for pong
                    close_timeout=5    # Reduced from 10 to prevent looping closes
                ) as websocket:
                    logger.info("✅ Connected to AIS Stream!\n")
                    
                    # Reset reconnection counter on successful connection
                    self.reconnect_attempts = 0
                    
                    # Send subscription message
                    await self._subscribe(websocket)
                    
                    # Start concurrent message processor if enabled
                    if self.enable_concurrent:
                        self.processing_task = asyncio.create_task(self._batch_processor())
                    
                    # Listen for messages
                    await self._listen(websocket)
                    
            except (websockets.exceptions.WebSocketException, 
                    websockets.exceptions.ConnectionClosed,
                    ConnectionResetError,
                    asyncio.TimeoutError) as e:
                
                if not self.running:
                    break
                
                # Skip logging if it's just a graceful close (no close frame is normal)
                if "no close frame" not in str(e).lower():
                    logger.warning(f"⚠️  Connection lost: {type(e).__name__}")
                else:
                    logger.debug(f"Connection closed gracefully")
                
                # Calculate exponential backoff delay
                self.reconnect_attempts += 1
                delay = min(2 ** self.reconnect_attempts, self.max_reconnect_delay)
                
                if "no close frame" not in str(e).lower():
                    logger.info(f"🔄 Reconnecting in {delay} seconds... (attempt {self.reconnect_attempts})")
                
                # Cancel processing task if exists
                if self.processing_task and not self.processing_task.done():
                    self.processing_task.cancel()
                    try:
                        await self.processing_task
                    except asyncio.CancelledError:
                        pass
                
                await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"❌ Unexpected error: {e}")
                import traceback
                traceback.print_exc()
                
                if not self.running:
                    break
                
                # Wait before retry on unexpected errors
                await asyncio.sleep(10)
    
    def stop(self):
        """Stop the AIS client and prevent reconnection."""
        logger.info("Stopping AIS client...")
        self.running = False
        
        if self.processing_task and not self.processing_task.done():
            self.processing_task.cancel()
    
    async def _subscribe(self, websocket):
        """Subscribe to ALL 30 regions worldwide (no regional fallback)."""
        from config import REGIONS
        
        # Subscribe to ALL regions at once for worldwide tracking
        bounding_boxes = list(REGIONS.values())
        
        subscribe_message = {
            "APIKey": AIS_API_KEY,
            "BoundingBoxes": bounding_boxes,
            "FilterMessageTypes": ["PositionReport", "ShipStaticData"]
        }
        
        await websocket.send(json.dumps(subscribe_message))
        logger.info(f"📡 Subscribed to {len(bounding_boxes)} worldwide regions")
        logger.info("📡 Listening for vessel data...\n")
    
    async def _listen(self, websocket):
        """Listen for and process incoming AIS messages."""
        while True:
            try:
                message_json = await websocket.recv()
                message = json.loads(message_json)
                
                if self.enable_concurrent:
                    # Add to queue for batch processing
                    self.message_queue.append(message)
                else:
                    # Process immediately
                    await self._process_message(message)
                
            except json.JSONDecodeError as e:
                logger.debug(f"JSON decode error: {e}")
            except KeyError as e:
                logger.debug(f"Missing key in message: {e}")
            except Exception as e:
                logger.warning(f"Error processing message: {e}")
    
    async def _batch_processor(self):
        """Process messages in batches for better performance."""
        while True:
            try:
                if len(self.message_queue) >= self.batch_size:
                    # Process batch
                    batch_size = min(self.batch_size, len(self.message_queue))
                    batch = [self.message_queue.popleft() for _ in range(batch_size)]
                    
                    # Process messages concurrently with gather
                    await asyncio.gather(*[self._process_message(msg) for msg in batch], return_exceptions=True)
                    
                    # Log batch completion
                    logger.debug(f"Processed batch of {batch_size} messages")
                else:
                    # Small delay to avoid busy waiting
                    await asyncio.sleep(0.01)
                    
            except Exception as e:
                logger.warning(f"Batch processor error: {e}")
    
    async def _process_message(self, message: dict):
        """
        Process incoming AIS message.
        
        Args:
            message: Parsed AIS message dictionary
        """
        message_type = message.get("MessageType")
        
        if message_type == "ShipStaticData":
            await self._handle_static_data(message)
        elif message_type == "PositionReport":
            await self._handle_position_report(message)
    
    async def _handle_static_data(self, message: dict):
        """Handle ship static data messages with enhanced information extraction."""
        static_data = message["Message"]["ShipStaticData"]
        mmsi = static_data["UserID"]
        ship_type = static_data.get("Type")
        
        # Debug: Log ship type information
        if ship_type is not None:
            logger.debug(f"Received ship_type {ship_type} for vessel {mmsi}")
        
        # Accept if we have space or already tracking
        if len(self.vessels) < self.max_vessels or mmsi in self.vessels:
            self.static_count += 1
            
            # Create or get vessel
            if mmsi not in self.vessels:
                self.vessels[mmsi] = Vessel(mmsi=mmsi)
            
            # Extract dimensions
            dimension_data = static_data.get("Dimension", {})
            
            # Process ETA data (optimized - single try/except)
            eta_string = self._parse_eta(static_data.get("Eta"))
            
            # Update static data with comprehensive information
            old_ship_type = self.vessels[mmsi].ship_type
            self.vessels[mmsi].update_static_data(
                name=static_data.get("Name"),
                destination=static_data.get("Destination"),
                ship_type=ship_type,
                imo=static_data.get("ImoNumber"),
                callsign=static_data.get("CallSign"),
                dimension_to_bow=dimension_data.get("A"),
                dimension_to_stern=dimension_data.get("B"),
                dimension_to_port=dimension_data.get("C"),
                dimension_to_starboard=dimension_data.get("D"),
                eta=eta_string
            )
            
            # Log when ship type is updated via static data
            if ship_type is not None and old_ship_type != ship_type:
                logger.debug(f"Static data updated ship_type for {mmsi} ({static_data.get('Name', 'Unknown')}): {old_ship_type} -> {ship_type}")
            
            # Calculate length and width from dimensions
            if dimension_data:
                a = dimension_data.get("A", 0) or 0
                b = dimension_data.get("B", 0) or 0
                c = dimension_data.get("C", 0) or 0
                d = dimension_data.get("D", 0) or 0
                
                if a and b:
                    self.vessels[mmsi].length = float(a + b)
                if c and d:
                    self.vessels[mmsi].width = float(c + d)
            
            # Call callback
            if self.on_static_data:
                self.on_static_data(self.vessels[mmsi])
            
            # Log tanker types with more info
            vessel = self.vessels[mmsi]
            if vessel.is_tanker():
                dims = f"{vessel.get_dimensions()}" if vessel.length else "Unknown size"
                logger.info(f"📋 ✅ TANKER {vessel.name} [{dims}] → {vessel.destination or 'Unknown'}")
    
    async def _handle_position_report(self, message: dict):
        """Handle position report messages with enhanced data extraction."""
        position_data = message["Message"]["PositionReport"]
        mmsi = position_data["UserID"]
        
        # Accept if we have space or already tracking
        if mmsi in self.vessels or len(self.vessels) < self.max_vessels:
            self.position_count += 1
            
            # Create or get vessel
            if mmsi not in self.vessels:
                self.vessels[mmsi] = Vessel(mmsi=mmsi)
            
            # Update position with comprehensive data
            self.vessels[mmsi].update_position(
                lat=position_data["Latitude"],
                lon=position_data["Longitude"],
                speed=position_data.get("Sog"),  # Speed over ground
                course=position_data.get("Cog"),  # Course over ground
                heading=position_data.get("TrueHeading"),
                rot=position_data.get("Rot"),  # Rate of turn
                navigational_status=position_data.get("NavigationalStatus"),
                position_accuracy=position_data.get("PositionAccuracy"),
                timestamp=datetime.now(timezone.utc).strftime("%H:%M:%S")
            )
            
            # Update ship type if available
            if position_data.get("ShipType"):
                old_ship_type = self.vessels[mmsi].ship_type
                self.vessels[mmsi].ship_type = position_data["ShipType"]
                
                # Log when ship type is updated
                if old_ship_type != self.vessels[mmsi].ship_type:
                    logger.debug(f"Updated ship_type for {mmsi}: {old_ship_type} -> {self.vessels[mmsi].ship_type}")
            
            # Call callback
            if self.on_position_update:
                self.on_position_update(self.vessels[mmsi])
            
            # Log position with enhanced info
            vessel = self.vessels[mmsi]
            is_tanker = "🛢️" if vessel.is_tanker() else "🚢"
            nav_status = vessel.get_navigational_status_text() if vessel.navigational_status is not None else "Unknown"
            
            logger.info(f"{is_tanker} {vessel.name or mmsi} | "
                       f"{vessel.lat:.4f}, {vessel.lon:.4f} | "
                       f"{vessel.speed or 0:.1f} kts @ {vessel.course or 0:.0f}° | "
                       f"{nav_status}")
            
            # Print summary periodically
            await self._print_summary()
    
    async def _print_summary(self):
        """Print periodic summary of tracked vessels."""
        if time.time() - self.last_summary_time > 45:
            active = sum(1 for v in self.vessels.values() if v.has_position())
            tanker_count = sum(1 for v in self.vessels.values() 
                             if v.has_position() and v.is_tanker())
            
            logger.info(f"\n{'='*70}")
            logger.info(f"📊 STATS: {active} vessels ({tanker_count} tankers)")
            logger.info(f"   Positions: {self.position_count} | Static data: {self.static_count}")
            logger.info(f"{'='*70}\n")
            
            self.last_summary_time = time.time()
    
    def get_vessels(self) -> Dict[int, Vessel]:
        """Get all tracked vessels."""
        return self.vessels
    
    def get_active_vessels(self) -> Dict[int, Vessel]:
        """Get vessels with valid position data."""
        return {mmsi: vessel for mmsi, vessel in self.vessels.items() 
                if vessel.has_position()}
    
    @staticmethod
    def _parse_eta(eta_data: Optional[dict]) -> Optional[str]:
        """
        Optimized ETA parsing with minimal type checks.
        
        Args:
            eta_data: ETA data from AIS message
            
        Returns:
            Formatted ETA string or None
        """
        if not eta_data:
            return None
        
        try:
            if isinstance(eta_data, dict):
                month = eta_data.get("Month", 0)
                day = eta_data.get("Day", 0)
                
                if month > 0 and day > 0:
                    hour = eta_data.get("Hour", 24)
                    minute = eta_data.get("Minute", 60)
                    
                    if hour < 24 and minute < 60:
                        return f"{month:02d}-{day:02d} {hour:02d}:{minute:02d}"
                    else:
                        return f"{month:02d}-{day:02d}"
            else:
                return str(eta_data)
        except Exception:
            return None
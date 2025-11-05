"""
AIS Client for connecting to AIS Stream WebSocket and processing vessel data.
"""

import asyncio
import websockets
import json
import time
from datetime import datetime, timezone
from typing import Dict, Callable, Optional
import logging

from config import AIS_API_KEY, AIS_URL, TANKER_TYPES
from models.vessel import Vessel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AISClient:
    """
    WebSocket client for AIS Stream service.
    
    Handles connection, subscription, and message processing for real-time vessel data.
    """
    
    def __init__(self, 
                 region_bounds: list,
                 max_vessels: int = 100,
                 on_static_data: Optional[Callable] = None,
                 on_position_update: Optional[Callable] = None):
        """
        Initialize AIS client.
        
        Args:
            region_bounds: Bounding box for tracking [[south, west], [north, east]]
            max_vessels: Maximum number of vessels to track
            on_static_data: Callback for static data messages
            on_position_update: Callback for position update messages
        """
        self.region_bounds = region_bounds
        self.max_vessels = max_vessels
        self.on_static_data = on_static_data
        self.on_position_update = on_position_update
        
        self.vessels: Dict[int, Vessel] = {}
        self.position_count = 0
        self.static_count = 0
        self.last_summary_time = time.time()
        
    async def connect(self):
        """Establish WebSocket connection and start listening for messages."""
        logger.info("Connecting to AIS Stream...")
        logger.info(f"Tracking region: {self.region_bounds}")
        logger.info(f"Max vessels: {self.max_vessels}\n")
        
        try:
            async with websockets.connect(AIS_URL) as websocket:
                logger.info("✅ Connected to AIS Stream!\n")
                
                # Send subscription message
                await self._subscribe(websocket)
                
                # Listen for messages
                await self._listen(websocket)
                
        except websockets.exceptions.WebSocketException as e:
            logger.error(f"WebSocket error: {e}")
            logger.info("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)
            await self.connect()  # Reconnect
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    
    async def _subscribe(self, websocket):
        """Send subscription message to AIS Stream."""
        subscribe_message = {
            "APIKey": AIS_API_KEY,
            "BoundingBoxes": [self.region_bounds],
            "FilterMessageTypes": ["PositionReport", "ShipStaticData"]
        }
        
        await websocket.send(json.dumps(subscribe_message))
        logger.info("📡 Subscription active. Listening for vessel data...\n")
    
    async def _listen(self, websocket):
        """Listen for and process incoming AIS messages."""
        while True:
            try:
                message_json = await websocket.recv()
                message = json.loads(message_json)
                await self._process_message(message)
                
            except json.JSONDecodeError as e:
                logger.debug(f"JSON decode error: {e}")
            except KeyError as e:
                logger.debug(f"Missing key in message: {e}")
            except Exception as e:
                logger.warning(f"Error processing message: {e}")
    
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
        """Handle ship static data messages (name, destination, etc.)."""
        static_data = message["Message"]["ShipStaticData"]
        mmsi = static_data["UserID"]
        ship_type = static_data.get("Type")
        
        # Accept if we have space or already tracking
        if len(self.vessels) < self.max_vessels or mmsi in self.vessels:
            self.static_count += 1
            
            # Create or get vessel
            if mmsi not in self.vessels:
                self.vessels[mmsi] = Vessel(mmsi=mmsi)
            
            # Update static data
            self.vessels[mmsi].update_static_data(
                name=static_data.get("Name"),
                destination=static_data.get("Destination"),
                ship_type=ship_type
            )
            
            # Call callback
            if self.on_static_data:
                self.on_static_data(self.vessels[mmsi])
            
            # Log tanker types
            if ship_type in TANKER_TYPES:
                logger.info(f"📋 ✅ TANKER {self.vessels[mmsi].name} → {self.vessels[mmsi].destination}")
    
    async def _handle_position_report(self, message: dict):
        """Handle position report messages (GPS coordinates, speed, etc.)."""
        position_data = message["Message"]["PositionReport"]
        mmsi = position_data["UserID"]
        
        # Accept if we have space or already tracking
        if mmsi in self.vessels or len(self.vessels) < self.max_vessels:
            self.position_count += 1
            
            # Create or get vessel
            if mmsi not in self.vessels:
                self.vessels[mmsi] = Vessel(mmsi=mmsi)
            
            # Update position
            self.vessels[mmsi].update_position(
                lat=position_data["Latitude"],
                lon=position_data["Longitude"],
                speed=position_data.get("Sog"),
                course=position_data.get("Cog"),
                timestamp=datetime.now(timezone.utc).strftime("%H:%M:%S")
            )
            
            # Update ship type if available
            if position_data.get("ShipType"):
                self.vessels[mmsi].ship_type = position_data["ShipType"]
            
            # Call callback
            if self.on_position_update:
                self.on_position_update(self.vessels[mmsi])
            
            # Log position
            vessel = self.vessels[mmsi]
            is_tanker = "🛢️" if vessel.is_tanker(TANKER_TYPES) else "🚢"
            logger.info(f"{is_tanker} {vessel.name or mmsi} | "
                       f"{vessel.lat:.3f}, {vessel.lon:.3f} | "
                       f"{vessel.speed or 0:.1f} kts | Type {vessel.ship_type}")
            
            # Print summary periodically
            await self._print_summary()
    
    async def _print_summary(self):
        """Print periodic summary of tracked vessels."""
        if time.time() - self.last_summary_time > 45:
            active = sum(1 for v in self.vessels.values() if v.has_position())
            tanker_count = sum(1 for v in self.vessels.values() 
                             if v.has_position() and v.is_tanker(TANKER_TYPES))
            
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
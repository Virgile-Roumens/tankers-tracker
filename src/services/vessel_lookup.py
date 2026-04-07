"""
Vessel Lookup Service - Search for individual vessels by MMSI.

Uses multiple sources in order:
1. Tracker's in-memory cache (fastest)
2. SQLite database (previously tracked vessels)
3. AIS Stream WebSocket (live query with timeout)
"""

import asyncio
import json
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)


def lookup_vessel_in_tracker(mmsi: int, tracker_manager) -> Optional[dict]:
    """
    Check if a vessel exists in the tracker's in-memory cache or database.
    
    Args:
        mmsi: Vessel MMSI number (integer)
        tracker_manager: The global TrackerManager instance
        
    Returns:
        Vessel dict (from to_dict()) if found, None otherwise
    """
    if not tracker_manager or not tracker_manager.tracker:
        return None
    
    tracker = tracker_manager.tracker
    
    # Check vessel_service which has in-memory cache backed by SQLite
    if hasattr(tracker, 'vessel_service'):
        vessel = tracker.vessel_service.get_vessel(mmsi)
        if vessel:
            logger.info(f"Found MMSI {mmsi} in tracker database: {vessel.name or 'Unknown'}")
            return vessel.to_dict()
    
    return None


def lookup_vessel_via_websocket(mmsi: str, timeout: float = 12.0) -> Optional[dict]:
    """
    Look up a vessel by opening a short-lived AIS Stream WebSocket connection
    filtered to the specific MMSI.
    
    Args:
        mmsi: MMSI number as string (9 digits)
        timeout: Max seconds to wait for vessel data
        
    Returns:
        Normalized vessel dict if found, None otherwise
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_websocket_lookup(mmsi, timeout))
        finally:
            loop.close()
    except Exception as e:
        logger.warning(f"WebSocket lookup failed for MMSI {mmsi}: {e}")
        return None


async def _websocket_lookup(mmsi: str, timeout: float) -> Optional[dict]:
    """
    Open a temporary WebSocket connection to AIS Stream to find a specific vessel.
    Uses FiltersShipMMSI to only receive data for the target vessel.
    """
    try:
        import websockets
    except ImportError:
        logger.error("websockets library not available for MMSI lookup")
        return None
    
    from config import AIS_API_KEY, AIS_URL
    
    subscribe_message = {
        "APIKey": AIS_API_KEY,
        "BoundingBoxes": [[[-90, -180], [90, 180]]],  # Worldwide
        "FiltersShipMMSI": [mmsi],
        "FilterMessageTypes": ["PositionReport", "ShipStaticData"]
    }
    
    try:
        async with websockets.connect(
            AIS_URL,
            ping_interval=10,
            ping_timeout=5,
            close_timeout=3
        ) as ws:
            await ws.send(json.dumps(subscribe_message))
            logger.info(f"🔍 WebSocket lookup: listening for MMSI {mmsi} (timeout: {timeout}s)")
            
            vessel_data = {"mmsi": int(mmsi)}
            has_position = False
            has_static = False
            start_time = asyncio.get_event_loop().time()
            
            while (asyncio.get_event_loop().time() - start_time) < timeout:
                try:
                    remaining = timeout - (asyncio.get_event_loop().time() - start_time)
                    if remaining <= 0:
                        break
                    
                    message_json = await asyncio.wait_for(
                        ws.recv(), 
                        timeout=min(remaining, 3.0)
                    )
                    message = json.loads(message_json)
                    
                    msg_type = message.get("MessageType", "")
                    meta = message.get("MetaData", {})
                    msg_mmsi = str(meta.get("MMSI", ""))
                    
                    if msg_mmsi != mmsi:
                        continue
                    
                    # Extract common metadata
                    ship_name = (meta.get("ShipName") or "").strip()
                    if ship_name and (not vessel_data.get("name") or vessel_data["name"] == "Unknown"):
                        vessel_data["name"] = ship_name
                    vessel_data["last_update"] = meta.get("time_utc", "")
                    
                    msg_body = message.get("Message", {})
                    
                    if msg_type == "ShipStaticData":
                        ship_data = msg_body.get("ShipStaticData", {})
                        name = (ship_data.get("Name") or "").strip()
                        if name:
                            vessel_data["name"] = name
                        vessel_data["imo"] = ship_data.get("ImoNumber", 0)
                        vessel_data["callsign"] = (ship_data.get("CallSign") or "").strip()
                        vessel_data["ship_type"] = ship_data.get("Type", 0)
                        vessel_data["destination"] = (ship_data.get("Destination") or "").strip()
                        
                        # Parse ETA
                        eta_obj = ship_data.get("Eta", {})
                        if eta_obj and isinstance(eta_obj, dict):
                            month = eta_obj.get("Month", 0)
                            day = eta_obj.get("Day", 0)
                            hour = eta_obj.get("Hour", 0)
                            minute = eta_obj.get("Minute", 0)
                            if month and day:
                                vessel_data["eta"] = f"{month:02d}-{day:02d} {hour:02d}:{minute:02d}"
                        
                        vessel_data["draught"] = ship_data.get("MaximumStaticDraught", 0)
                        
                        # Dimensions
                        dim = ship_data.get("Dimension", {})
                        if dim and isinstance(dim, dict):
                            a = dim.get("A", 0) or 0
                            b = dim.get("B", 0) or 0
                            c = dim.get("C", 0) or 0
                            d = dim.get("D", 0) or 0
                            if a + b > 0:
                                vessel_data["length"] = a + b
                            if c + d > 0:
                                vessel_data["width"] = c + d
                        
                        has_static = True
                        logger.info(f"  📋 Got static data for MMSI {mmsi}: {vessel_data.get('name')}")
                        
                    elif msg_type == "PositionReport":
                        pos = msg_body.get("PositionReport", {})
                        lat = pos.get("Latitude", meta.get("latitude", 0))
                        lon = pos.get("Longitude", meta.get("longitude", 0))
                        
                        if lat and lon and not (lat == 0 and lon == 0):
                            vessel_data["lat"] = lat
                            vessel_data["lon"] = lon
                            vessel_data["speed"] = pos.get("Sog", 0)
                            vessel_data["course"] = pos.get("Cog", 0)
                            vessel_data["heading"] = pos.get("TrueHeading", 0)
                            vessel_data["navigational_status"] = pos.get("NavigationalStatus", 15)
                            has_position = True
                            logger.info(f"  📍 Got position for MMSI {mmsi}: {lat:.4f}, {lon:.4f}")
                    
                    # If we have both position and static data, return immediately
                    if has_position and has_static:
                        logger.info(f"✅ Complete data for MMSI {mmsi}")
                        return _normalize_for_frontend(vessel_data)
                    
                    # If we at least have position, we can return
                    if has_position:
                        # Wait a bit more for static data, but don't block too long
                        elapsed = asyncio.get_event_loop().time() - start_time
                        if elapsed > timeout * 0.7:
                            return _normalize_for_frontend(vessel_data)
                    
                except asyncio.TimeoutError:
                    # No message received in this interval, continue waiting
                    continue
                except json.JSONDecodeError:
                    continue
            
            # Timeout reached - return whatever we have
            if has_position or has_static:
                logger.info(f"⏱️ Timeout reached for MMSI {mmsi}, returning partial data")
                return _normalize_for_frontend(vessel_data)
            
            logger.info(f"❌ No AIS data received for MMSI {mmsi} within {timeout}s")
            return None
    
    except Exception as e:
        logger.warning(f"WebSocket lookup error for MMSI {mmsi}: {e}")
        return None


def _normalize_for_frontend(data: dict) -> dict:
    """
    Normalize raw vessel data into a dict compatible with Vessel.to_dict() format.
    This ensures the JavaScript frontend can display the vessel consistently.
    """
    ship_type_code = data.get("ship_type", 0) or 0
    
    # Determine vessel category
    category = "Other"
    display_class = "Other"
    if isinstance(ship_type_code, int):
        if 80 <= ship_type_code <= 89:
            category = "Tanker"
            display_class = "Tanker"
        elif 70 <= ship_type_code <= 79:
            category = "Cargo"
            display_class = "Cargo Ship"
    
    # Get ship type display name
    ship_type_name = "Unknown"
    try:
        from enums.ship_type import ShipType
        ship_type_enum = ShipType.from_code(ship_type_code) if ship_type_code else None
        if ship_type_enum:
            ship_type_name = ship_type_enum.display_name
            display_class = ship_type_name
    except (ImportError, Exception):
        pass
    
    return {
        "mmsi": data.get("mmsi", 0),
        "lat": data.get("lat"),
        "lon": data.get("lon"),
        "name": data.get("name", "Unknown"),
        "imo": data.get("imo"),
        "callsign": data.get("callsign"),
        "speed": data.get("speed"),
        "course": data.get("course"),
        "heading": data.get("heading"),
        "rot": data.get("rot"),
        "navigational_status": data.get("navigational_status"),
        "destination": data.get("destination"),
        "eta": data.get("eta"),
        "ship_type": ship_type_code,
        "ship_type_name": ship_type_name,
        "length": data.get("length"),
        "width": data.get("width"),
        "draught": data.get("draught"),
        "cargo": data.get("cargo"),
        "deadweight": data.get("deadweight"),
        "gross_tonnage": data.get("gross_tonnage"),
        "vessel_category": category,
        "is_bulk_carrier": False,
        "bulk_carrier_class": None,
        "tanker_class": None,
        "display_class": display_class,
        "last_update": data.get("last_update"),
        "first_seen": data.get("last_update"),
        "update_count": 1,
        "searched": True,
    }

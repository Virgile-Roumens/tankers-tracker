#!/usr/bin/env python3
"""
Test script to verify ship_type data is being saved correctly to the database.
"""

import logging
import os
from utils.vessel_database import VesselDatabase
from utils.vessel_info_service import VesselInfoService  
from models.vessel import Vessel
from config import TANKER_TYPES, DATABASE_PATH

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_ship_type_persistence():
    """Test that ship_type data persists correctly in database."""
    
    print("🧪 Testing ship_type database persistence...")
    
    # Clean test - remove existing database
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
        print(f"🗑️  Removed existing database: {DATABASE_PATH}")
    
    # Create vessel service
    service = VesselInfoService(use_database=True)
    
    # Create test vessels with different ship types
    test_vessels = [
        {"mmsi": 123456789, "name": "TEST TANKER", "ship_type": 80, "lat": 25.0, "lon": 55.0},
        {"mmsi": 987654321, "name": "TEST CARGO", "ship_type": 70, "lat": 25.1, "lon": 55.1},
        {"mmsi": 555666777, "name": "TEST CONTAINER", "ship_type": 71, "lat": 25.2, "lon": 55.2},
    ]
    
    # Add test vessels
    for data in test_vessels:
        vessel = Vessel(mmsi=data["mmsi"])
        vessel.name = data["name"]
        vessel.ship_type = data["ship_type"]
        vessel.lat = data["lat"]
        vessel.lon = data["lon"]
        vessel.update_count = 1
        vessel.last_update = "12:00:00"
        vessel.first_seen = "12:00:00"
        
        service.update_vessel(vessel)
        print(f"➕ Added {vessel.name} (Type: {vessel.ship_type})")
    
    # Close and reopen service to test persistence  
    service.close()
    print("💾 Saved and closed database")
    
    # Reopen database and check if ship_types persisted
    service2 = VesselInfoService(use_database=True)
    reloaded_vessels = service2.get_all_vessels()
    
    print(f"📖 Reloaded {len(reloaded_vessels)} vessels")
    
    # Check each vessel
    success = True
    for data in test_vessels:
        mmsi = data["mmsi"]
        if mmsi in reloaded_vessels:
            vessel = reloaded_vessels[mmsi]
            expected_type = data["ship_type"]
            actual_type = vessel.ship_type
            
            if actual_type == expected_type:
                is_tanker = vessel.is_tanker(TANKER_TYPES)
                tanker_icon = "🛢️" if is_tanker else "🚢"
                print(f"✅ {tanker_icon} {vessel.name}: Type {actual_type} (correct)")
            else:
                print(f"❌ {vessel.name}: Expected type {expected_type}, got {actual_type}")
                success = False
        else:
            print(f"❌ Vessel {mmsi} not found after reload")
            success = False
    
    # Count tankers
    tankers = [v for v in reloaded_vessels.values() if v.is_tanker(TANKER_TYPES)]
    print(f"🛢️  Found {len(tankers)} tankers after reload")
    
    service2.close()
    
    if success:
        print("🎉 SUCCESS: ship_type persistence test passed!")
    else:
        print("❌ FAILED: ship_type persistence test failed!")
    
    return success

if __name__ == "__main__":
    test_ship_type_persistence()
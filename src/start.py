"""
Tankers Tracker - Simple Launcher

Just run this file to start the tracker!
Use the dropdown in the map to switch regions.
"""

import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Start the tankers tracker with web interface."""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║              🌍 TANKER TRACKER v2.0 - WORLDWIDE MODE                 ║
║              Real-time Global AIS Vessel Tracking                    ║
╚══════════════════════════════════════════════════════════════════════╝

🚀 Starting worldwide tracker...

💡 How to use:
   1. Map will open in your browser automatically
   2. Pan/zoom freely across the world
   3. Map updates automatically every 30 seconds
   4. Press Ctrl+C here to stop
    """)
    
    # Change to src directory
    os.chdir(Path(__file__).parent)
    
    try:
        from web_interface import TankersWebServer
        
        # Start server on port 8000
        server = TankersWebServer(port=8000, host='localhost')
        server.start(auto_open=True)
        
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
ULTRA FAST STARTUP - No reloader, minimal output
"""

from main import app
import logging

if __name__ == '__main__':
    # Suppress all Flask logging for maximum speed
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    
    print("🚀 Attendance System - FAST MODE")
    print("📱 Access: http://localhost:5000")
    print("🔒 IP Address: Hidden for security")
    print("⚡ Press CTRL+C to quit")
    print("-" * 40)
    
    # Ultra-fast configuration
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,        # No debug mode = faster
        use_reloader=False, # No auto-restart = faster
        threaded=True       # Multi-threading = faster
    )

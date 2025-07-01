#!/usr/bin/env python3
"""
Attendance System - Safe Startup Script
Hides sensitive network information from logs
"""

import os
import sys
import logging
from main import app

def start_app():
    """Start the Flask app with privacy protection"""
    
    # Suppress Flask's default startup messages
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    
    # Custom startup message (no IP exposure)
    print("\n" + "="*60)
    print("🎯 ATTENDANCE SYSTEM - STARTING...")
    print("="*60)
    print("📋 Project: Face Recognition Attendance System")
    print("🔒 Privacy: Network details hidden")
    print("💻 Local Access: http://localhost:5000")
    print("📱 Mobile: Use your network scanner to find IP")
    print("="*60)
    print("✅ Ready! Open your browser and navigate to localhost:5000")
    print("🔄 Press Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    try:
        # Start the app without revealing network details
        app.run(
            debug=True, 
            host='0.0.0.0', 
            port=5000,
            use_reloader=False  # Prevents duplicate startup messages
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        print("👋 Thanks for using the Attendance System!")

if __name__ == '__main__':
    start_app()

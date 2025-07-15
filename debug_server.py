#!/usr/bin/env python3
"""
Run Flask app with debug mode to see actual errors
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_debug_server():
    """Run Flask app in debug mode"""
    print("STARTING FLASK APP IN DEBUG MODE")
    print("="*50)
    
    try:
        # Import main module
        import main
        app = main.app
        
        # Initialize database
        print("Initializing database...")
        main.init_db()
        print("✓ Database initialized")
        
        # Configure for debug
        app.config['DEBUG'] = True
        app.config['TESTING'] = True
        
        print("✓ Flask app configured for debug")
        print("\nStarting server on http://127.0.0.1:5000")
        print("Press Ctrl+C to stop")
        print("="*50)
        
        # Run the app
        app.run(host='127.0.0.1', port=5000, debug=True)
        
    except Exception as e:
        print(f"✗ Error starting server: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_debug_server()

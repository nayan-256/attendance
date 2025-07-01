#!/usr/bin/env python3
"""
Quick Test - Simple Flask startup to diagnose issues
"""

from main import app

if __name__ == '__main__':
    print("🔧 Testing Flask startup...")
    try:
        app.run(host='127.0.0.1', port=5000, debug=False)
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Try: python test_startup.py")

#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_flask_app():
    """Test the Flask application"""
    
    print("=== Testing Flask Application ===")
    
    try:
        # Import and test the Flask app
        print("1. Importing Flask app...")
        import main
        app = main.app
        print("   ✅ Flask app imported successfully")
        
        # Test app configuration
        print("2. Testing app configuration...")
        print(f"   Secret key: {'Set' if app.secret_key else 'Not set'}")
        print(f"   Upload folder: {app.config.get('UPLOAD_FOLDER', 'Not set')}")
        
        # Test database initialization
        print("3. Testing database...")
        import sqlite3
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"   Tables: {[t[0] for t in tables]}")
        conn.close()
        
        # Test routes
        print("4. Testing routes...")
        with app.test_client() as client:
            # Test home route
            response = client.get('/')
            print(f"   Home route (/): {response.status_code}")
            
            # Test student_login route
            response = client.get('/student_login')
            print(f"   Student login route (/student_login): {response.status_code}")
            
            # Test student_home route (should redirect)
            response = client.get('/student_home')
            print(f"   Student home route (/student_home): {response.status_code}")
            
            # Test student_home route with session
            with client.session_transaction() as sess:
                sess['student_id'] = 'test123'
            response = client.get('/student_home')
            print(f"   Student home with session: {response.status_code}")
        
        print("✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_flask_app()
    if success:
        print("\n🎉 Flask app is working correctly!")
    else:
        print("\n💥 Flask app has issues!")

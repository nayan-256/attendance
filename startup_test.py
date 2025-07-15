#!/usr/bin/env python3
"""
Simple test to check if Flask app can start without errors
"""
import sys
import os
import traceback

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_flask_startup():
    """Test if Flask app can start without errors"""
    print("TESTING FLASK APP STARTUP")
    print("="*40)
    
    try:
        # Step 1: Import main module
        print("1. Importing main module...")
        import main
        print("   ✓ Main module imported successfully")
        
        # Step 2: Check if app is created
        print("2. Checking Flask app...")
        app = main.app
        print(f"   ✓ Flask app created: {app}")
        print(f"   ✓ Secret key: {'Set' if app.secret_key else 'Not set'}")
        
        # Step 3: Check database initialization
        print("3. Testing database initialization...")
        main.init_db()
        print("   ✓ Database initialization successful")
        
        # Step 4: Test with test client
        print("4. Testing with test client...")
        with app.test_client() as client:
            print("   ✓ Test client created")
            
            # Test basic route
            response = client.get('/')
            print(f"   ✓ Root route status: {response.status_code}")
            
            # Test student login route
            response = client.get('/student_login')
            print(f"   ✓ Student login route status: {response.status_code}")
            
        print("\n✓ All startup tests passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Error during startup test: {e}")
        traceback.print_exc()
        return False

def test_specific_route():
    """Test the specific student_home route"""
    print("\n" + "="*40)
    print("TESTING STUDENT_HOME ROUTE")
    print("="*40)
    
    try:
        import main
        app = main.app
        
        with app.test_client() as client:
            # Test without session (should redirect)
            print("1. Testing without session...")
            response = client.get('/student_home')
            print(f"   Status: {response.status_code} (expecting 302 redirect)")
            
            # Test with session
            print("2. Testing with session...")
            with client.session_transaction() as sess:
                sess['student_id'] = 'test123'
            
            response = client.get('/student_home')
            print(f"   Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"   Response data: {response.data.decode()[:200]}")
                
        return True
        
    except Exception as e:
        print(f"\n✗ Error testing student_home: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    startup_ok = test_flask_startup()
    route_ok = test_specific_route()
    
    print("\n" + "="*40)
    print("FINAL SUMMARY")
    print("="*40)
    print(f"Startup Test: {'✓' if startup_ok else '✗'}")
    print(f"Route Test: {'✓' if route_ok else '✗'}")
    
    if startup_ok and route_ok:
        print("\n✓ Flask app appears to be working correctly!")
        print("The issue might be with the database or session handling.")
    else:
        print("\n✗ There are issues with the Flask app.")

if __name__ == "__main__":
    main()

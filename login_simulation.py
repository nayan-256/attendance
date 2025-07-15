#!/usr/bin/env python3
"""
Minimal test to simulate the exact student login process
"""
import sys
import os
import sqlite3
import traceback

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def simulate_student_login():
    """Simulate the exact student login process"""
    print("SIMULATING STUDENT LOGIN PROCESS")
    print("="*50)
    
    try:
        # Step 1: Import Flask app
        print("1. Importing Flask app...")
        from main import app
        from flask import session, url_for, redirect, render_template
        print("   ✓ Flask app imported successfully")
        
        # Step 2: Check database for users
        print("2. Checking database for users...")
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("SELECT student_id, password FROM users LIMIT 1")
        test_user = cur.fetchone()
        
        if test_user:
            print(f"   ✓ Found test user: {test_user['student_id']}")
            student_id = test_user['student_id']
            password = test_user['password']
        else:
            print("   ✗ No users found in database")
            return False
        
        conn.close()
        
        # Step 3: Test login process with Flask test client
        print("3. Testing login process...")
        with app.test_client() as client:
            # Simulate POST to student_login
            print("   - Posting login credentials...")
            response = client.post('/student_login', 
                                 data={'student_id': student_id, 'password': password},
                                 follow_redirects=False)
            
            print(f"   - Login response status: {response.status_code}")
            
            if response.status_code == 302:  # Redirect expected
                print("   ✓ Login successful, redirect received")
                
                # Check redirect location
                location = response.headers.get('Location', '')
                print(f"   - Redirect location: {location}")
                
                # Follow the redirect
                print("   - Following redirect...")
                response = client.get(location, follow_redirects=False)
                print(f"   - student_home response status: {response.status_code}")
                
                if response.status_code == 200:
                    print("   ✓ student_home loaded successfully")
                    return True
                else:
                    print(f"   ✗ student_home failed with status: {response.status_code}")
                    print(f"   Response data: {response.data.decode()[:500]}")
                    return False
                    
            else:
                print(f"   ✗ Login failed with status: {response.status_code}")
                print(f"   Response data: {response.data.decode()[:500]}")
                return False
                
    except Exception as e:
        print(f"✗ Error during simulation: {e}")
        traceback.print_exc()
        return False

def test_student_home_directly():
    """Test student_home route directly"""
    print("\nTESTING STUDENT_HOME ROUTE DIRECTLY")
    print("="*50)
    
    try:
        from main import app
        
        with app.test_client() as client:
            with client.session_transaction() as sess:
                # Set up session as if user is logged in
                sess['student_id'] = 'test_student'
            
            # Test student_home route
            print("Testing student_home with valid session...")
            response = client.get('/student_home')
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✓ student_home route works with valid session")
                return True
            else:
                print(f"✗ student_home failed: {response.status_code}")
                print(f"Response: {response.data.decode()[:500]}")
                return False
                
    except Exception as e:
        print(f"✗ Error testing student_home: {e}")
        traceback.print_exc()
        return False

def main():
    """Run simulation tests"""
    print("STUDENT LOGIN SIMULATION TEST")
    print("="*50)
    
    # Test 1: Simulate full login process
    login_ok = simulate_student_login()
    
    # Test 2: Test student_home directly
    home_ok = test_student_home_directly()
    
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Login Process: {'✓' if login_ok else '✗'}")
    print(f"Student Home: {'✓' if home_ok else '✗'}")
    
    if login_ok and home_ok:
        print("\n✓ All tests passed!")
        print("The issue might be in the browser or server setup.")
    else:
        print("\n✗ Some tests failed.")
        print("Check the errors above to identify the issue.")

if __name__ == "__main__":
    main()

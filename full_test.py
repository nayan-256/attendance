#!/usr/bin/env python3
"""
Complete test to identify the student login issue
"""
import sys
import os
import sqlite3
import traceback

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database():
    """Test database connectivity and structure"""
    print("="*50)
    print("TESTING DATABASE")
    print("="*50)
    
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Check tables
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cur.fetchall()]
        print(f"✓ Tables found: {tables}")
        
        if 'users' in tables:
            # Check users table structure
            cur.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in cur.fetchall()]
            print(f"✓ Users table columns: {columns}")
            
            # Check user count
            cur.execute("SELECT COUNT(*) FROM users")
            count = cur.fetchone()[0]
            print(f"✓ Total users: {count}")
            
            if count > 0:
                # Show sample user
                cur.execute("SELECT student_id, name, class_year, department FROM users LIMIT 1")
                user = cur.fetchone()
                print(f"✓ Sample user: {dict(user)}")
                
                # Test a specific user lookup
                cur.execute("SELECT * FROM users WHERE student_id = ? AND password = ?", 
                           (user['student_id'], 'password123'))
                test_user = cur.fetchone()
                if test_user:
                    print(f"✓ Test login possible for: {user['student_id']}")
                else:
                    print(f"✗ Test login failed for: {user['student_id']}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Database error: {e}")
        traceback.print_exc()
        return False

def test_flask_app():
    """Test Flask app creation and routes"""
    print("\n" + "="*50)
    print("TESTING FLASK APP")
    print("="*50)
    
    try:
        from main import app
        print("✓ Flask app imported successfully")
        
        # Test app context
        with app.app_context():
            print("✓ App context created successfully")
            
            # Test client
            with app.test_client() as client:
                print("✓ Test client created successfully")
                
                # Test student_login route
                print("\nTesting student_login route...")
                response = client.get('/student_login')
                print(f"  Status: {response.status_code}")
                if response.status_code == 200:
                    print("  ✓ student_login route works")
                else:
                    print(f"  ✗ student_login route failed: {response.status_code}")
                
                # Test student_home route (should redirect)
                print("\nTesting student_home route...")
                response = client.get('/student_home')
                print(f"  Status: {response.status_code}")
                if response.status_code in [200, 302]:
                    print("  ✓ student_home route accessible")
                else:
                    print(f"  ✗ student_home route failed: {response.status_code}")
                
        return True
        
    except Exception as e:
        print(f"✗ Flask app error: {e}")
        traceback.print_exc()
        return False

def test_template_rendering():
    """Test template rendering"""
    print("\n" + "="*50)
    print("TESTING TEMPLATE RENDERING")
    print("="*50)
    
    try:
        from main import app
        from flask import render_template
        
        with app.app_context():
            # Test student_home template
            print("Testing student_home.html template...")
            try:
                result = render_template('student_home.html', student_data={'name': 'Test User'})
                print("  ✓ student_home.html renders successfully")
            except Exception as e:
                print(f"  ✗ student_home.html error: {e}")
                
            # Test student_dashboard template
            print("Testing student_dashboard.html template...")
            try:
                result = render_template('student_dashboard.html', 
                                       student={'name': 'Test User'}, 
                                       attendance_records=[])
                print("  ✓ student_dashboard.html renders successfully")
            except Exception as e:
                print(f"  ✗ student_dashboard.html error: {e}")
                
        return True
        
    except Exception as e:
        print(f"✗ Template rendering error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("COMPREHENSIVE FLASK APP TEST")
    print("="*50)
    
    # Run tests
    db_ok = test_database()
    flask_ok = test_flask_app()
    template_ok = test_template_rendering()
    
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Database: {'✓' if db_ok else '✗'}")
    print(f"Flask App: {'✓' if flask_ok else '✗'}")
    print(f"Templates: {'✓' if template_ok else '✗'}")
    
    if db_ok and flask_ok and template_ok:
        print("\n✓ All tests passed! The issue might be elsewhere.")
    else:
        print("\n✗ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()

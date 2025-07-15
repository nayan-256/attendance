import sys
import os
import traceback

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from main import app
    import sqlite3
    from flask import session
    
    # Test the database connection
    print("Testing database connection...")
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    
    # Check if users table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cur.fetchone():
        print("✓ Users table exists")
        
        # Check if there are any students in the database
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
        print(f"✓ Found {user_count} users in database")
        
        # Show first few users
        cur.execute("SELECT student_id, name, class_year, department FROM users LIMIT 5")
        users = cur.fetchall()
        print("Sample users:")
        for user in users:
            print(f"  - ID: {user[0]}, Name: {user[1]}, Class: {user[2]}, Dept: {user[3]}")
    else:
        print("✗ Users table does not exist")
    
    conn.close()
    
    # Test if Flask app can be created
    print("\nTesting Flask app...")
    with app.app_context():
        print("✓ Flask app context created successfully")
    
    # Test if student_home route exists
    print("\nTesting routes...")
    with app.test_client() as client:
        # Test student_home route (should redirect to login)
        response = client.get('/student_home')
        print(f"student_home route status: {response.status_code}")
        
        # Test student_login route
        response = client.get('/student_login')
        print(f"student_login route status: {response.status_code}")
    
    print("\n✓ All basic tests passed!")
    
except Exception as e:
    print(f"✗ Error occurred: {e}")
    traceback.print_exc()

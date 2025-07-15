#!/usr/bin/env python3
"""
Debug version of student_home route to identify the exact issue
"""
import sys
import os
import sqlite3
import traceback

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_student_home():
    """Debug the student_home route step by step"""
    print("DEBUGGING STUDENT_HOME ROUTE")
    print("="*50)
    
    try:
        # Step 1: Import Flask and set up app
        print("1. Setting up Flask app...")
        from flask import Flask, session, render_template, redirect, url_for, flash
        import main
        app = main.app
        print("   ✓ Flask app ready")
        
        # Step 2: Check database
        print("2. Checking database...")
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Check if users table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cur.fetchone():
            print("   ✓ Users table exists")
            
            # Get a sample user
            cur.execute("SELECT student_id, name, class_year, department FROM users LIMIT 1")
            sample_user = cur.fetchone()
            
            if sample_user:
                print(f"   ✓ Sample user found: {sample_user['student_id']}")
                test_student_id = sample_user['student_id']
            else:
                print("   ✗ No users in database")
                return False
        else:
            print("   ✗ Users table does not exist")
            return False
            
        conn.close()
        
        # Step 3: Test the route logic
        print("3. Testing route logic...")
        
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['student_id'] = test_student_id
                
            # Test the route
            print("   - Making request to /student_home...")
            response = client.get('/student_home')
            print(f"   - Response status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✓ Route executed successfully")
                print(f"   - Response length: {len(response.data)} bytes")
                return True
            elif response.status_code == 302:
                print("   - Redirect received")
                location = response.headers.get('Location', '')
                print(f"   - Redirect to: {location}")
                return False
            else:
                print(f"   ✗ Unexpected status: {response.status_code}")
                # Print first 500 chars of response
                response_text = response.data.decode('utf-8', errors='ignore')
                print(f"   Response preview: {response_text[:500]}")
                return False
                
    except Exception as e:
        print(f"✗ Error during debug: {e}")
        traceback.print_exc()
        return False

def test_template_rendering():
    """Test template rendering separately"""
    print("\nTESTING TEMPLATE RENDERING")
    print("="*50)
    
    try:
        import main
        app = main.app
        
        with app.app_context():
            # Test rendering student_home.html
            print("1. Testing student_home.html...")
            from flask import render_template
            
            # Create mock student data
            mock_student = {
                'student_id': 'TEST123',
                'name': 'Test Student',
                'class_year': '2024',
                'department': 'Computer Science'
            }
            
            try:
                result = render_template('student_home.html', student=mock_student)
                print("   ✓ Template rendered successfully")
                print(f"   - Output length: {len(result)} characters")
                return True
            except Exception as e:
                print(f"   ✗ Template rendering failed: {e}")
                traceback.print_exc()
                return False
                
    except Exception as e:
        print(f"✗ Error during template test: {e}")
        traceback.print_exc()
        return False

def main():
    """Run debug tests"""
    route_ok = debug_student_home()
    template_ok = test_template_rendering()
    
    print("\n" + "="*50)
    print("DEBUG SUMMARY")
    print("="*50)
    print(f"Route Logic: {'✓' if route_ok else '✗'}")
    print(f"Template Rendering: {'✓' if template_ok else '✗'}")
    
    if route_ok and template_ok:
        print("\n✓ Both route and template work correctly!")
        print("The issue might be with the browser, server, or network.")
    else:
        print("\n✗ Found issues that need to be fixed.")

if __name__ == "__main__":
    main()

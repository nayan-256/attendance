#!/usr/bin/env python3
"""
Final test of the student login fix
"""
import sys
import os
import sqlite3

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_student_login_final():
    """Test the complete student login process"""
    print("TESTING STUDENT LOGIN FIX")
    print("="*50)
    
    try:
        # First, set up the database
        print("1. Setting up database...")
        
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        
        # Ensure test user exists
        cur.execute("SELECT * FROM users WHERE student_id = ?", ('test123',))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO users (student_id, password, name, class_year, department)
                VALUES (?, ?, ?, ?, ?)
            """, ('test123', 'password123', 'Test Student', '2024', 'Computer Science'))
            conn.commit()
            print("   ✓ Test user created")
        else:
            print("   ✓ Test user exists")
        
        conn.close()
        
        # Test Flask app
        print("2. Testing Flask app...")
        from main import app
        
        with app.test_client() as client:
            # Test login
            print("   - Testing login...")
            response = client.post('/student_login', 
                                 data={'student_id': 'test123', 'password': 'password123'},
                                 follow_redirects=False)
            
            if response.status_code == 302:
                print("   ✓ Login successful (redirect received)")
                
                # Test student_home
                print("   - Testing student_home...")
                with client.session_transaction() as sess:
                    sess['student_id'] = 'test123'
                
                response = client.get('/student_home')
                print(f"   - student_home status: {response.status_code}")
                
                if response.status_code == 200:
                    print("   ✓ student_home works correctly")
                    return True
                else:
                    print(f"   ✗ student_home failed: {response.status_code}")
                    return False
                    
            else:
                print(f"   ✗ Login failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test"""
    success = test_student_login_final()
    
    print("\n" + "="*50)
    print("TEST RESULT")
    print("="*50)
    
    if success:
        print("✓ STUDENT LOGIN FIX SUCCESSFUL!")
        print("\nThe internal server error should now be resolved.")
        print("You can run your Flask app and try logging in with:")
        print("  Student ID: test123")
        print("  Password: password123")
    else:
        print("✗ STUDENT LOGIN FIX FAILED!")
        print("\nThere are still issues that need to be resolved.")

if __name__ == "__main__":
    main()

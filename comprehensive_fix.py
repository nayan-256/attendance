#!/usr/bin/env python3
"""
Comprehensive fix for the student login issue
"""
import sqlite3
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_database_schema():
    """Fix the database schema to ensure all required columns exist"""
    print("FIXING DATABASE SCHEMA")
    print("="*50)
    
    try:
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        
        # Check if users table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cur.fetchone():
            print("Creating users table...")
            cur.execute('''CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                student_id TEXT,
                image_path TEXT,
                class_year TEXT,
                department TEXT,
                password TEXT
            )''')
            print("✓ Users table created")
        else:
            print("✓ Users table exists")
            
            # Check and add missing columns
            cur.execute("PRAGMA table_info(users)")
            existing_cols = [col[1] for col in cur.fetchall()]
            
            required_cols = ['student_id', 'password', 'name', 'class_year', 'department']
            for col in required_cols:
                if col not in existing_cols:
                    cur.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
                    print(f"✓ Added {col} column")
        
        # Check if there are any users
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
        
        if user_count == 0:
            print("Adding test users...")
            test_users = [
                ('test123', 'password123', 'Test Student', '2024', 'Computer Science'),
                ('student1', 'pass123', 'John Doe', '2024', 'Electronics'),
                ('student2', 'pass123', 'Jane Smith', '2023', 'Mechanical')
            ]
            
            for user in test_users:
                cur.execute("""
                    INSERT INTO users (student_id, password, name, class_year, department)
                    VALUES (?, ?, ?, ?, ?)
                """, user)
                print(f"✓ Added user: {user[0]}")
                
            conn.commit()
            print("✓ Test users added")
        else:
            print(f"✓ Found {user_count} users in database")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Database fix error: {e}")
        return False

def create_fixed_student_home_route():
    """Create a fixed version of the student_home route"""
    print("\nCREATING FIXED STUDENT_HOME ROUTE")
    print("="*50)
    
    fixed_route = '''
@app.route('/student_home')
def student_home():
    """Fixed student home route with proper error handling"""
    try:
        # Check if student is logged in
        if 'student_id' not in session:
            flash("Please log in to access this page", "warning")
            return redirect(url_for('student_login'))
        
        student_id = session.get('student_id')
        
        # Connect to database
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Get student details
        cur.execute("SELECT * FROM users WHERE student_id = ?", (student_id,))
        student = cur.fetchone()
        
        if not student:
            flash("Student not found in database", "error")
            session.clear()  # Clear invalid session
            conn.close()
            return redirect(url_for('student_login'))
        
        # Convert to dict for template
        student_data = {
            'student_id': student['student_id'],
            'name': student['name'] or 'Unknown',
            'class_year': student['class_year'] or 'N/A',
            'department': student['department'] or 'N/A'
        }
        
        conn.close()
        
        # Render template with student data
        return render_template('student_home.html', student=student_data)
        
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Error in student_home route: {e}")
        flash("An error occurred. Please try again.", "error")
        return redirect(url_for('student_login'))
'''
    
    print("Fixed route code:")
    print(fixed_route)
    
    # Write to a file for reference
    with open('fixed_student_home_route.py', 'w') as f:
        f.write(fixed_route)
    
    print("✓ Fixed route saved to 'fixed_student_home_route.py'")
    return True

def test_fix():
    """Test the fix"""
    print("\nTESTING THE FIX")
    print("="*50)
    
    try:
        # Test database
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        
        # Test login query
        cur.execute("SELECT * FROM users WHERE student_id=? AND password=?", ('test123', 'password123'))
        user = cur.fetchone()
        
        if user:
            print("✓ Login query works")
            
            # Test student_home query
            cur.execute("SELECT * FROM users WHERE student_id = ?", ('test123',))
            student = cur.fetchone()
            
            if student:
                print("✓ Student home query works")
                print(f"✓ Student data: {student}")
                return True
            else:
                print("✗ Student home query failed")
                return False
        else:
            print("✗ Login query failed")
            return False
            
        conn.close()
        
    except Exception as e:
        print(f"✗ Test error: {e}")
        return False

def main():
    """Run all fixes"""
    print("COMPREHENSIVE FIX FOR STUDENT LOGIN ISSUE")
    print("="*60)
    
    # Run fixes
    db_ok = fix_database_schema()
    route_ok = create_fixed_student_home_route()
    test_ok = test_fix()
    
    print("\n" + "="*60)
    print("FIX SUMMARY")
    print("="*60)
    print(f"Database Schema: {'✓' if db_ok else '✗'}")
    print(f"Route Fix: {'✓' if route_ok else '✗'}")
    print(f"Test: {'✓' if test_ok else '✗'}")
    
    if db_ok and route_ok and test_ok:
        print("\n✓ All fixes applied successfully!")
        print("\nNext steps:")
        print("1. Copy the fixed route code to your main.py file")
        print("2. Restart your Flask application")
        print("3. Try logging in with: student_id='test123', password='password123'")
    else:
        print("\n✗ Some fixes failed. Check the errors above.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Initialize database with proper schema and test data
"""
import sqlite3
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_database():
    """Set up database with proper schema and test data"""
    print("SETTING UP DATABASE")
    print("="*50)
    
    try:
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        
        # Create users table with all required columns
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            student_id TEXT,
            image_path TEXT,
            class_year TEXT,
            department TEXT,
            password TEXT
        )''')
        
        # Create attendance table
        cur.execute('''CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            timestamp TEXT,
            status TEXT DEFAULT 'Present',
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        
        # Create admin table
        cur.execute('''CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )''')
        
        # Create teachers table
        cur.execute('''CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )''')
        
        # Check if columns exist and add if missing
        cur.execute("PRAGMA table_info(users)")
        existing_cols = [col[1] for col in cur.fetchall()]
        
        required_cols = ['student_id', 'password', 'name', 'class_year', 'department']
        for col in required_cols:
            if col not in existing_cols:
                cur.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
                print(f"Added {col} column")
        
        # Add test users if none exist
        cur.execute("SELECT COUNT(*) FROM users")
        if cur.fetchone()[0] == 0:
            test_users = [
                ('test123', 'password123', 'Test Student', '2024', 'Computer Science'),
                ('student1', 'pass123', 'John Doe', '2024', 'Electronics'),
                ('student2', 'pass123', 'Jane Smith', '2023', 'Mechanical'),
                ('student3', 'pass123', 'Bob Wilson', '2024', 'Civil'),
                ('student4', 'pass123', 'Alice Brown', '2023', 'Information Technology')
            ]
            
            for user in test_users:
                cur.execute("""
                    INSERT INTO users (student_id, password, name, class_year, department)
                    VALUES (?, ?, ?, ?, ?)
                """, user)
                print(f"Added user: {user[0]} ({user[2]})")
        
        # Add default admin if not exists
        cur.execute("SELECT * FROM admin WHERE username='admin'")
        if not cur.fetchone():
            cur.execute("INSERT INTO admin (username, password) VALUES (?, ?)", ('admin', 'admin123'))
            print("Added default admin")
        
        conn.commit()
        conn.close()
        
        print("✓ Database setup complete")
        return True
        
    except Exception as e:
        print(f"✗ Database setup error: {e}")
        return False

def test_database():
    """Test the database setup"""
    print("\nTESTING DATABASE")
    print("="*50)
    
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Test users table
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
        print(f"Users in database: {user_count}")
        
        # Test sample login
        cur.execute("SELECT * FROM users WHERE student_id=? AND password=?", ('test123', 'password123'))
        user = cur.fetchone()
        
        if user:
            print("✓ Test login works")
            print(f"  Student ID: {user['student_id']}")
            print(f"  Name: {user['name']}")
            print(f"  Class: {user['class_year']}")
            print(f"  Department: {user['department']}")
        else:
            print("✗ Test login failed")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Database test error: {e}")
        return False

def main():
    """Run database setup and test"""
    setup_ok = setup_database()
    test_ok = test_database()
    
    print("\n" + "="*50)
    print("SETUP SUMMARY")
    print("="*50)
    print(f"Database Setup: {'✓' if setup_ok else '✗'}")
    print(f"Database Test: {'✓' if test_ok else '✗'}")
    
    if setup_ok and test_ok:
        print("\n✓ Database is ready!")
        print("\nTest credentials:")
        print("  Student ID: test123")
        print("  Password: password123")
        print("\nYou can now run your Flask app and try logging in.")
    else:
        print("\n✗ Database setup failed.")

if __name__ == "__main__":
    main()

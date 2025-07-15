#!/usr/bin/env python3
"""
Check database schema and fix any issues
"""
import sqlite3
import traceback

def check_and_fix_database():
    """Check database schema and fix any issues"""
    print("CHECKING DATABASE SCHEMA")
    print("="*50)
    
    try:
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        
        # Check if users table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cur.fetchone():
            print("✓ Users table exists")
            
            # Check table structure
            cur.execute("PRAGMA table_info(users)")
            columns = cur.fetchall()
            print("\nUsers table columns:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # Check for required columns
            column_names = [col[1] for col in columns]
            required_columns = ['student_id', 'password', 'name', 'class_year', 'department']
            
            missing_columns = []
            for col in required_columns:
                if col not in column_names:
                    missing_columns.append(col)
            
            if missing_columns:
                print(f"\nMissing columns: {missing_columns}")
                print("Adding missing columns...")
                
                for col in missing_columns:
                    try:
                        cur.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
                        print(f"  ✓ Added {col} column")
                    except Exception as e:
                        print(f"  ✗ Failed to add {col}: {e}")
                        
                conn.commit()
            else:
                print("\n✓ All required columns exist")
                
            # Check if there are any users
            cur.execute("SELECT COUNT(*) FROM users")
            user_count = cur.fetchone()[0]
            print(f"\nTotal users in database: {user_count}")
            
            if user_count == 0:
                print("No users found. Adding test user...")
                cur.execute("""
                    INSERT INTO users (student_id, password, name, class_year, department)
                    VALUES (?, ?, ?, ?, ?)
                """, ('test123', 'password123', 'Test Student', '2024', 'Computer Science'))
                conn.commit()
                print("✓ Test user added")
            else:
                # Show sample users
                cur.execute("SELECT student_id, name, class_year, department FROM users LIMIT 3")
                users = cur.fetchall()
                print("\nSample users:")
                for user in users:
                    print(f"  - {user[0]}: {user[1]} ({user[2]}, {user[3]})")
                    
        else:
            print("✗ Users table does not exist")
            print("Running database initialization...")
            
            # Run init_db function
            import main
            main.init_db()
            print("✓ Database initialized")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Database error: {e}")
        traceback.print_exc()
        return False

def test_login_query():
    """Test the login query"""
    print("\nTESTING LOGIN QUERY")
    print("="*50)
    
    try:
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        
        # Get first user
        cur.execute("SELECT student_id, password FROM users LIMIT 1")
        user = cur.fetchone()
        
        if user:
            student_id, password = user
            print(f"Testing login for: {student_id}")
            
            # Test the exact query used in student_login
            cur.execute("SELECT * FROM users WHERE student_id=? AND password=?", (student_id, password))
            result = cur.fetchone()
            
            if result:
                print("✓ Login query works")
                
                # Test the query used in student_home
                cur.execute("SELECT * FROM users WHERE student_id = ?", (student_id,))
                result = cur.fetchone()
                
                if result:
                    print("✓ Student home query works")
                    return True
                else:
                    print("✗ Student home query failed")
                    return False
                    
            else:
                print("✗ Login query failed")
                return False
                
        else:
            print("✗ No users found to test")
            return False
            
        conn.close()
        
    except Exception as e:
        print(f"✗ Query test error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all checks"""
    db_ok = check_and_fix_database()
    login_ok = test_login_query()
    
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Database Schema: {'✓' if db_ok else '✗'}")
    print(f"Login Queries: {'✓' if login_ok else '✗'}")
    
    if db_ok and login_ok:
        print("\n✓ Database is properly configured!")
        print("The issue might be elsewhere.")
    else:
        print("\n✗ Database issues found and fixed.")
        print("Try running the Flask app again.")

if __name__ == "__main__":
    main()

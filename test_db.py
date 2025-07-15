import sqlite3
import os

print("Testing database connection...")

try:
    # Check if database file exists
    db_path = 'database.db'
    if os.path.exists(db_path):
        print(f"✅ Database file exists: {db_path}")
    else:
        print(f"❌ Database file missing: {db_path}")
        
    # Test database connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"✅ Database tables: {[table[0] for table in tables]}")
    
    # Check users table
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"✅ Users in database: {user_count}")
    
    # Check if student_id column exists
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    print(f"✅ User table columns: {column_names}")
    
    conn.close()
    print("✅ Database connection test successful!")
    
except Exception as e:
    print(f"❌ Database error: {e}")
    import traceback
    traceback.print_exc()

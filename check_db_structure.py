import sqlite3

# Check database structure
conn = sqlite3.connect('database.db')
cur = conn.cursor()

# Get all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print("Tables in database:")
for table in tables:
    print(f"  - {table[0]}")

# Check users table structure
cur.execute("PRAGMA table_info(users)")
columns = cur.fetchall()
print("\nUsers table structure:")
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

# Check if there are any users
cur.execute("SELECT COUNT(*) FROM users")
user_count = cur.fetchone()[0]
print(f"\nTotal users: {user_count}")

if user_count > 0:
    # Show first few users
    cur.execute("SELECT student_id, name, class_year, department FROM users LIMIT 5")
    users = cur.fetchall()
    print("\nFirst 5 users:")
    for user in users:
        print(f"  - ID: {user[0]}, Name: {user[1]}, Class: {user[2]}, Dept: {user[3]}")

conn.close()

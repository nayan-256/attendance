import sqlite3

# Connect to the database (or create if it doesn't exist)
conn = sqlite3.connect('../database/attendance.db')
cursor = conn.cursor()

# Create table if not exists
cursor.execute('''CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL
                )''')

# Commit and close connection
conn.commit()
conn.close()

print("✅ Database setup complete!")

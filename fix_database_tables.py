import sqlite3

# Connect to the correct database that main.py uses
conn = sqlite3.connect('database.db')
cur = conn.cursor()

print("Adding missing tables to database.db...")

try:
    # Create teachers table
    cur.execute('''CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')
    print("✅ Teachers table created/verified")

    # Create subjects table  
    cur.execute('''CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_name TEXT UNIQUE,
        subject_code TEXT UNIQUE,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    print("✅ Subjects table created/verified")

    # Create teacher_subjects mapping table
    cur.execute('''CREATE TABLE IF NOT EXISTS teacher_subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id INTEGER,
        subject_id INTEGER,
        FOREIGN KEY(teacher_id) REFERENCES teachers(id),
        FOREIGN KEY(subject_id) REFERENCES subjects(id),
        UNIQUE(teacher_id, subject_id)
    )''')
    print("✅ Teacher-Subjects mapping table created/verified")

    # Insert default teacher
    cur.execute("INSERT OR IGNORE INTO teachers (username, password) VALUES (?, ?)", ('teacher1', 'teacher123'))
    print("✅ Default teacher added")

    # Insert default subjects
    subjects = [
        ('Mathematics', 'MATH101', 'Basic Mathematics'),
        ('Physics', 'PHY101', 'Basic Physics'),
        ('Chemistry', 'CHEM101', 'Basic Chemistry'),
        ('Computer Science', 'CS101', 'Introduction to Computer Science'),
        ('English', 'ENG101', 'English Language and Literature'),
        ('History', 'HIST101', 'World History')
    ]

    for name, code, desc in subjects:
        cur.execute("INSERT OR IGNORE INTO subjects (subject_name, subject_code, description) VALUES (?, ?, ?)", 
                   (name, code, desc))
    print("✅ Default subjects added")

    conn.commit()

    # Verify tables exist
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cur.fetchall()]
    print(f"\n📋 Database now contains tables: {', '.join(tables)}")

    # Check counts
    if 'teachers' in tables:
        cur.execute("SELECT COUNT(*) FROM teachers")
        print(f"   - Teachers: {cur.fetchone()[0]} records")

    if 'subjects' in tables:
        cur.execute("SELECT COUNT(*) FROM subjects") 
        print(f"   - Subjects: {cur.fetchone()[0]} records")

    print("\n🎉 Database setup completed successfully!")
    print("You can now access /manage_teachers and /manage_subjects")

except Exception as e:
    print(f"❌ Error: {e}")
    
finally:
    conn.close()

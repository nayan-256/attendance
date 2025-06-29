#!/usr/bin/env python3
"""
Database initialization script to create all required tables
"""
import sqlite3
import os

def init_database():
    """Initialize the database with all required tables"""
    
    # Database path
    db_path = "attendance.db"
    
    print("Initializing database...")
    
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Create users table
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            student_id TEXT,
            image_path TEXT,
            class_year TEXT,
            department TEXT,
            password TEXT
        )''')
        print("✅ Users table created/verified")

        # Create attendance table
        cur.execute('''CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            timestamp TEXT,
            status TEXT DEFAULT 'Present',
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        print("✅ Attendance table created/verified")

        # Create admin table
        cur.execute('''CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )''')
        print("✅ Admin table created/verified")

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

        # Insert default admin if not exists
        cur.execute("SELECT * FROM admin WHERE username='admin'")
        if not cur.fetchone():
            cur.execute("INSERT INTO admin (username, password) VALUES (?, ?)", ('admin', 'admin123'))
            print("✅ Default admin created")

        # Insert default teacher if not exists
        cur.execute("SELECT * FROM teachers WHERE username='teacher1'")
        if not cur.fetchone():
            cur.execute("INSERT INTO teachers (username, password) VALUES (?, ?)", ('teacher1', 'teacher123'))
            print("✅ Default teacher created")

        # Insert default subjects
        default_subjects = [
            ('Mathematics', 'MATH101', 'Basic Mathematics'),
            ('Physics', 'PHY101', 'Basic Physics'),
            ('Chemistry', 'CHEM101', 'Basic Chemistry'),
            ('Computer Science', 'CS101', 'Introduction to Computer Science'),
            ('English', 'ENG101', 'English Language and Literature'),
            ('History', 'HIST101', 'World History')
        ]
        
        subjects_added = 0
        for subject_name, subject_code, description in default_subjects:
            cur.execute("SELECT * FROM subjects WHERE subject_code=?", (subject_code,))
            if not cur.fetchone():
                cur.execute("INSERT INTO subjects (subject_name, subject_code, description) VALUES (?, ?, ?)", 
                           (subject_name, subject_code, description))
                subjects_added += 1
        
        if subjects_added > 0:
            print(f"✅ {subjects_added} default subjects created")

        conn.commit()
        
        # Verify tables
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cur.fetchall()
        print(f"\n📋 Database contains {len(tables)} tables:")
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cur.fetchone()[0]
            print(f"   - {table[0]}: {count} records")
        
        conn.close()
        print(f"\n🎉 Database initialization completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    init_database()

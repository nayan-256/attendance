import sqlite3

# Force create all tables
conn = sqlite3.connect('attendance.db')
cur = conn.cursor()

# Create teachers table
cur.execute('''CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)''')

# Create subjects table  
cur.execute('''CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_name TEXT UNIQUE,
    subject_code TEXT UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

# Create teacher_subjects mapping table
cur.execute('''CREATE TABLE IF NOT EXISTS teacher_subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id INTEGER,
    subject_id INTEGER,
    FOREIGN KEY(teacher_id) REFERENCES teachers(id),
    FOREIGN KEY(subject_id) REFERENCES subjects(id),
    UNIQUE(teacher_id, subject_id)
)''')

# Insert default teacher
cur.execute("INSERT OR IGNORE INTO teachers (username, password) VALUES (?, ?)", ('teacher1', 'teacher123'))

# Insert default subjects
subjects = [
    ('Mathematics', 'MATH101', 'Basic Mathematics'),
    ('Physics', 'PHY101', 'Basic Physics'),
    ('Chemistry', 'CHEM101', 'Basic Chemistry'),
    ('Computer Science', 'CS101', 'Introduction to Computer Science')
]

for name, code, desc in subjects:
    cur.execute("INSERT OR IGNORE INTO subjects (subject_name, subject_code, description) VALUES (?, ?, ?)", (name, code, desc))

conn.commit()

# Verify
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cur.fetchall()]
print("Tables in database:", tables)

if 'teachers' in tables:
    cur.execute("SELECT COUNT(*) FROM teachers")
    print(f"Teachers count: {cur.fetchone()[0]}")

if 'subjects' in tables:
    cur.execute("SELECT COUNT(*) FROM subjects") 
    print(f"Subjects count: {cur.fetchone()[0]}")

conn.close()
print("Database setup complete!")

import sqlite3

# Connect to the database
conn = sqlite3.connect('database.db')
cur = conn.cursor()

print("Removing old subjects from database...")

# Old subjects to remove
old_subjects = [
    'Mathematics',
    'Physics', 
    'Chemistry',
    'Computer Science'
]

try:
    for subject_name in old_subjects:
        # Remove from teacher_subjects mapping first
        cur.execute("""
            DELETE FROM teacher_subjects 
            WHERE subject_id IN (
                SELECT id FROM subjects WHERE subject_name = ?
            )
        """, (subject_name,))
        
        # Remove the subject
        cur.execute("DELETE FROM subjects WHERE subject_name = ?", (subject_name,))
        print(f"✅ Removed: {subject_name}")
    
    conn.commit()
    
    # Show remaining subjects
    cur.execute("SELECT subject_name, subject_code FROM subjects ORDER BY subject_name")
    remaining = cur.fetchall()
    
    print(f"\n📋 Remaining subjects in database: {len(remaining)}")
    for subject in remaining:
        print(f"   - {subject[0]} ({subject[1]})")
    
    print("\n🎉 Old subjects removed successfully!")
    
except Exception as e:
    print(f"❌ Error removing subjects: {e}")
    
finally:
    conn.close()

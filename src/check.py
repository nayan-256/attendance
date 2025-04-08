import sqlite3

# Path to your database file
db_path = r"C:\Users\attar\OneDrive\Desktop\project\Attendance_System\database\attendance.db"

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Fetch all attendance records
cursor.execute("SELECT * FROM attendance")
rows = cursor.fetchall()

# Print results
print("\n📌 Attendance Records:")
print("-------------------------------------------------")
print("| ID  | Name               | Date       | Time  |")
print("-------------------------------------------------")
for row in rows:
    print(f"| {row[0]:<3} | {row[1]:<18} | {row[2]} | {row[3]} |")
print("-------------------------------------------------")

conn.close()

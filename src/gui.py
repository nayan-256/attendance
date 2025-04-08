import sqlite3
import pandas as pd

conn = sqlite3.connect("../database/attendance.db")
df = pd.read_sql_query("SELECT * FROM attendance ORDER BY date DESC, time DESC", conn)
conn.close()

print(df)
df.to_csv("C:/Users/attar/OneDrive/Desktop/project/Attendance_System/reports/attendence.csv", index=False)
print("✅ Exported to attendence.csv")

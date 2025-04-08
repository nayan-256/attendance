import sqlite3
import pandas as pd

def fetch_attendance():
    conn = sqlite3.connect('../database/attendance.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM attendance")
    records = cursor.fetchall()

    df = pd.DataFrame(records, columns=['ID', 'Name', 'Date', 'Time'])
    conn.close()

    print(df)
    df.to_csv("../reports/attendance.csv", index=False)

fetch_attendance()

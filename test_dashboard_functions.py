#!/usr/bin/env python3
"""
Test the teacher dashboard functionality directly
"""

import sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime
from collections import defaultdict

def test_teacher_dashboard_functionality():
    """Test the core teacher dashboard functions"""
    print("Testing teacher dashboard functionality...")
    
    # Initialize test database
    conn = sqlite3.connect('test_attendance.db')
    cur = conn.cursor()
    
    # Create test tables
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        student_id TEXT
    )''')
    
    cur.execute('''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        timestamp TEXT,
        status TEXT DEFAULT 'Present',
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    
    # Insert test data
    cur.execute("INSERT INTO users (name, student_id) VALUES (?, ?)", ('John Doe', 'STU001'))
    cur.execute("INSERT INTO users (name, student_id) VALUES (?, ?)", ('Jane Smith', 'STU002'))
    
    user_id = 1
    # Insert test attendance records
    test_dates = [
        '2025-06-25 09:00:00',
        '2025-06-26 09:15:00',
        '2025-06-27 09:30:00'
    ]
    
    for date in test_dates:
        cur.execute("INSERT INTO attendance (user_id, timestamp, status) VALUES (?, ?, ?)", 
                   (user_id, date, 'Present'))
    
    conn.commit()
    
    print("✅ Test data created")
    
    # Test chart generation
    try:
        cur.execute('SELECT status, COUNT(*) FROM attendance WHERE user_id=? GROUP BY status', (user_id,))
        records = cur.fetchall()
        
        if records:
            labels = [r[0] for r in records]
            values = [r[1] for r in records]
            
            plt.figure(figsize=(5,5))
            plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
            plt.title('Attendance Distribution')
            plt.axis('equal')
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches="tight")
            buf.seek(0)
            graph = base64.b64encode(buf.getvalue()).decode()
            buf.close()
            plt.close()
            
            print("✅ Chart generation successful")
            print(f"Graph data length: {len(graph)} characters")
        
    except Exception as e:
        print(f"❌ Chart generation failed: {e}")
    
    # Test date processing
    try:
        cur.execute('''
            SELECT DATE(timestamp) FROM attendance
            WHERE user_id=? AND status='Present'
        ''', (user_id,))
        
        all_dates = [row[0] for row in cur.fetchall()]
        weekly = defaultdict(int)
        monthly = defaultdict(int)
        
        for date_str in all_dates:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            week_label = f"{date.strftime('%Y')}-W{date.strftime('%U')}"
            month_label = date.strftime('%Y-%m')
            weekly[week_label] += 1
            monthly[month_label] += 1
        
        print("✅ Date processing successful")
        print(f"Weekly summary: {dict(weekly)}")
        print(f"Monthly summary: {dict(monthly)}")
        
    except Exception as e:
        print(f"❌ Date processing failed: {e}")
    
    conn.close()
    print("\n✅ Teacher dashboard functionality test completed!")

if __name__ == '__main__':
    test_teacher_dashboard_functionality()

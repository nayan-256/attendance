import os
import numpy as np
import sqlite3
import matplotlib
matplotlib.use('Agg')  # Set backend before importing pyplot
import matplotlib.pyplot as plt
import io
import base64
import csv
import pandas as pd
import uuid
from datetime import datetime,timedelta
from collections import defaultdict
from flask import Flask, flash, send_file, render_template, request, redirect, url_for, session,jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = '123'

# Dummy admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

# Optional imports that might cause issues
CV2_AVAILABLE = False
FACE_RECOGNITION_AVAILABLE = False

print("Warning: Face recognition features disabled - teacher dashboard and basic functionality available")

# === Setup Database ===
def init_db():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    # Create users table
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        student_id TEXT,  -- Make sure student_id exists
        image_path TEXT
    )''')

    # Create attendance table
    cur.execute('''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        timestamp TEXT,
        status TEXT DEFAULT 'Present',
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    # Create admin table
    cur.execute('''CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')

    # Check existing columns in users table
    cur.execute("PRAGMA table_info(users)")
    existing_cols = [col[1] for col in cur.fetchall()]

    if 'class_year' not in existing_cols:
        cur.execute("ALTER TABLE users ADD COLUMN class_year TEXT")
    if 'department' not in existing_cols:
        cur.execute("ALTER TABLE users ADD COLUMN department TEXT")
    if 'password' not in existing_cols:
        cur.execute("ALTER TABLE users ADD COLUMN password TEXT")

    # Insert default admin if not exists
    cur.execute("SELECT * FROM admin WHERE username='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO admin (username, password) VALUES (?, ?)", ('admin', 'admin123'))

    # Create teachers table
    cur.execute('''CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')

    # Insert a default teacher
    cur.execute("SELECT * FROM teachers WHERE username='teacher1'")
    if not cur.fetchone():
        cur.execute("INSERT INTO teachers (username, password) VALUES (?, ?)", ('teacher1', 'teacher123'))

    conn.commit()
    conn.close()

init_db()

@app.route('/', endpoint='home')
def home():
    return render_template('index.html')

@app.route('/teacher_login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        username = request.form['username']        #Username: teacher1
        password = request.form['password']        #Password: teacher123
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM teachers WHERE username=? AND password=?", (username, password))
        teacher = cur.fetchone()
        conn.close()
        if teacher:
            session['teacher_logged_in'] = True
            session['teacher_username'] = username
            return redirect(url_for('teacher_dashboard'))
        else:
            flash('Invalid teacher credentials', 'error')
    return render_template('teacher_login.html')

@app.route('/teacher_dashboard', methods=['GET', 'POST'])
def teacher_dashboard():
    if not session.get('teacher_logged_in'):
        return redirect(url_for('teacher_login'))
    
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('SELECT id, name, student_id FROM users')
    students = cur.fetchall()
    graph = None
    selected_student = None
    labels = []
    values = []
    legend_labels = []
    attendance_dates = []
    weekly_summary = {}
    monthly_summary = {}
    start_date = None
    end_date = None

    if request.method == 'POST':
        student_id = request.form.get('student_id')
        student_name = request.form.get('student_name')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        if student_id:
            cur.execute('SELECT id, name FROM users WHERE id=?', (student_id,))
            student = cur.fetchone()
        elif student_name:
            cur.execute('SELECT id, name FROM users WHERE name=?', (student_name,))
            student = cur.fetchone()
        else:
            student = None

        if student:
            selected_student = student[0]
            
            # Pie chart generation with error handling
            try:
                if start_date and end_date:
                    cur.execute('''
                        SELECT status, COUNT(*) FROM attendance
                        WHERE user_id = ? AND DATE(timestamp) BETWEEN ? AND ?
                        GROUP BY status
                    ''', (selected_student, start_date, end_date))
                else:
                    cur.execute('SELECT status, COUNT(*) FROM attendance WHERE user_id=? GROUP BY status', (selected_student,))
                
                records = cur.fetchall()
                if records:
                    labels = [r[0] for r in records]
                    values = [r[1] for r in records]
                    legend_labels = [f"{label} ({value})" for label, value in zip(labels, values)]
                    
                    plt.figure(figsize=(5,5))
                    patches, texts, autotexts = plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
                    plt.legend(patches, legend_labels, loc="best")
                    plt.title('Attendance Distribution')
                    plt.axis('equal')
                    
                    buf = io.BytesIO()
                    plt.savefig(buf, format='png', bbox_inches="tight")
                    buf.seek(0)
                    graph = base64.b64encode(buf.getvalue()).decode()
                    buf.close()
                    plt.close()
                    
            except Exception as e:
                print(f"Error generating chart: {e}")
                graph = None

            # Attendance Dates
            try:
                if start_date and end_date:
                    cur.execute('''
                        SELECT DATE(timestamp) FROM attendance
                        WHERE user_id=? AND (status='Present' OR status='Check-In')
                        AND DATE(timestamp) BETWEEN ? AND ?
                        ORDER BY timestamp DESC
                    ''', (selected_student, start_date, end_date))
                else:
                    cur.execute('''
                        SELECT DATE(timestamp) FROM attendance
                        WHERE user_id=? AND (status='Present' OR status='Check-In')
                        ORDER BY timestamp DESC
                    ''', (selected_student,))
                attendance_dates = [row[0] for row in cur.fetchall()]
            except Exception as e:
                print(f"Error fetching attendance dates: {e}")
                attendance_dates = []

            # Weekly and Monthly Summary
            try:
                if start_date and end_date:
                    cur.execute('''
                        SELECT DATE(timestamp) FROM attendance
                        WHERE user_id=? AND (status='Present' OR status='Check-In')
                        AND DATE(timestamp) BETWEEN ? AND ?
                    ''', (selected_student, start_date, end_date))
                else:
                    cur.execute('''
                        SELECT DATE(timestamp) FROM attendance
                        WHERE user_id=? AND (status='Present' OR status='Check-In')
                    ''', (selected_student,))

                all_dates = [row[0] for row in cur.fetchall()]
                weekly = defaultdict(int)
                monthly = defaultdict(int)
                
                for date_str in all_dates:
                    try:
                        date = datetime.strptime(date_str, '%Y-%m-%d')
                        week_label = f"{date.strftime('%Y')}-W{date.strftime('%U')}"
                        month_label = date.strftime('%Y-%m')
                        weekly[week_label] += 1
                        monthly[month_label] += 1
                    except ValueError as ve:
                        print(f"Error parsing date {date_str}: {ve}")
                        continue

                weekly_summary = dict(weekly)
                monthly_summary = dict(monthly)
                
            except Exception as e:
                print(f"Error generating summaries: {e}")
                weekly_summary = {}
                monthly_summary = {}

    conn.close()
    
    return render_template(
        'teacher_dashboard.html',
        students=students,
        graph=graph,
        selected_student=selected_student,
        attendance_dates=attendance_dates,
        start_date=start_date,
        end_date=end_date,
        weekly_summary=weekly_summary,
        monthly_summary=monthly_summary
    )

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('teacher_logged_in', None)
    session.pop('teacher_username', None)
    session.pop('student_id', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    print("Starting Flask app (face recognition disabled)...")
    print("Teacher login: username=teacher1, password=teacher123")
    app.run(debug=True, port=5000)

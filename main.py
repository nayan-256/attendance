import os
import cv2
import pickle
import face_recognition
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
import io
import base64
import csv
import pandas as pd
from datetime import datetime
from flask import Flask, flash, send_file, render_template, request, redirect, url_for, session


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = '123'

# Dummy admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'
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
        cur.execute("ALTER TABLE users ADD COLUMN password TEXT")   # ✅ Add this line

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


@app.route('/')
def home():
    return render_template('index.html')
    
from flask import flash, redirect, render_template, request, session, url_for
@app.route('/student_dashboard')
def student_dashboard():
    student_id = session.get('student_id')
    if not student_id:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Get student info
    cur.execute("SELECT * FROM users WHERE student_id = ?", (student_id,))
    student = cur.fetchone()

    # Get recent attendance
    cur.execute('''
        SELECT DATE(timestamp) AS date, TIME(timestamp) AS time, status
        FROM attendance
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT 10
    ''', (student['id'],))
    attendance_records = cur.fetchall()

    conn.close()
    return render_template('student_dashboard.html', student=student, attendance_records=attendance_records)
@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        student_id = request.form['student_id']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE student_id=? AND password=?", (student_id, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session['student_id'] = student_id
            return redirect(url_for('profile'))  # or student_dashboard if you have that
        else:
            flash("Invalid credentials", "danger")

    return render_template('student_login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Replace these with secure checks or a user database in real apps
        if username == 'admin' and password == 'admin123':
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'error')  # Flash the error message
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('logged_in', None)             # Admin
    session.pop('teacher_logged_in', None)     # Teacher
    session.pop('teacher_username', None)      # Optional, if used
    session.pop('student_id', None)            # ✅ Student logout

    return redirect(url_for('home'))

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

@app.route('/teacher_logout')
def teacher_logout():
    session.pop('teacher_logged_in', None)
    session.pop('teacher_username', None)
    return redirect(url_for('teacher_login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        student_id = request.form['student_id']
        class_year = request.form['class_year']
        department = request.form['department']
        password = request.form['password']
        image_data = request.form['captured_image']

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()

        # 🔍 Check for existing student ID
        cur.execute("SELECT * FROM users WHERE student_id = ?", (student_id,))
        existing_user = cur.fetchone()

        if existing_user:
            conn.close()
            # 🔁 Send user back to the form with a message
            return render_template('register.html', error="🚫 Student ID already registered!")

        if image_data:
            header, encoded = image_data.split(',', 1)
            image_bytes = base64.b64decode(encoded)

            filename = f"{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

            with open(filepath, 'wb') as f:
                f.write(image_bytes)

            # ✅ Save to database
            cur.execute("INSERT INTO users (name, student_id, class_year,department,password, image_path) VALUES (?, ?, ?, ?,?,?)",
                    (name, student_id, class_year,department,password, filepath))
            conn.commit()
            conn.close()
            session['student_id'] = student_id   # ✅ Add this line

            return redirect(url_for('profile'))

    # GET or fallback render
    return render_template('register.html')

@app.route('/profile')
def profile():
    student_id = session.get('student_id')  # assuming student logs in and session is set
    if not student_id:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE student_id = ?", (student_id,))
    user = cur.fetchone()
    conn.close()

    return render_template('profile.html', user=user)

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    student_id = session.get('student_id')
    if not student_id:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        class_year = request.form['class_year']
        department = request.form['department']

        # ✅ Update the database
        cur.execute("""
            UPDATE users SET name = ?, class_year = ?, department = ? WHERE student_id = ?
        """, (name, class_year, department, student_id))

        conn.commit()
        conn.close()

        return redirect(url_for('profile'))

    # GET: load existing user data
    cur.execute("SELECT * FROM users WHERE student_id = ?", (student_id,))
    user = cur.fetchone()
    conn.close()

    return render_template('edit_profile.html', user=user)



@app.route('/attendance')
def attendance():
    known_encodings = []
    known_ids = []

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT id, image_path FROM users")
    users = cur.fetchall()

    for user in users:
        img = face_recognition.load_image_file(user[1])
        encodings = face_recognition.face_encodings(img)
        if encodings:
            known_encodings.append(encodings[0])
            known_ids.append(user[0])

    cap = cv2.VideoCapture(0)
    success, frame = cap.read()
    cap.release()

    face_locations = face_recognition.face_locations(frame)
    face_encodings = face_recognition.face_encodings(frame, face_locations)

    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_encodings, face_encoding)
        if True in matches:
            matched_id = known_ids[matches.index(True)]
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute("INSERT INTO attendance (user_id, timestamp, status) VALUES (?, ?, ?)", (matched_id, timestamp, "Present"))
            conn.commit()

    conn.close()
    return render_template('attendance.html')

@app.route('/view_attendance', methods=['GET', 'POST'])
def view_attendance():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    # Get filter values from the form
    name = request.form.get('name')
    class_year = request.form.get('class_year')
    department = request.form.get('department')

    # Base query
    query = '''
        SELECT u.name, u.student_id, u.class_year, u.department,
               a.timestamp
        FROM attendance a
        JOIN users u ON a.user_id = u.id
        WHERE 1=1
    '''
    params = []

    if name:
        query += " AND u.name LIKE ?"
        params.append(f"%{name}%")

    if class_year:
        query += " AND u.class_year = ?"
        params.append(class_year)

    if department:
        query += " AND u.department = ?"
        params.append(department)

    cur.execute(query, params)
    records = cur.fetchall()
    conn.close()

    return render_template("attendance.html", records=records)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    # Ensure the user is logged in before proceeding
    if not session.get('logged_in'):
        return redirect(url_for('login'))  # Redirect to login page if not logged in
    
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    
    # Fetch all unique names and dates for the dropdowns
    cur.execute('SELECT DISTINCT name FROM users')
    names = cur.fetchall()
    
    cur.execute('SELECT DISTINCT DATE(timestamp) FROM attendance ORDER BY timestamp DESC')
    dates = cur.fetchall()
    
    # If a search is submitted, filter the records based on name and date
    records = []
    if request.method == 'POST':
        selected_name = request.form.get('name')
        selected_date = request.form.get('date')
        
        # Query for attendance records filtered by name and/or date
        query = '''
            SELECT 
                users.name,
                users.class_year, 
                users.department, 
                DATE(attendance.timestamp) AS date, 
                TIME(attendance.timestamp) AS time, 
                attendance.status 
            FROM attendance 
            JOIN users ON attendance.user_id = users.id
        '''
        conditions = []
        params = []
        
        if selected_name:
            conditions.append("users.name = ?")
            params.append(selected_name)
        
        if selected_date:
            conditions.append("DATE(attendance.timestamp) = ?")
            params.append(selected_date)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY attendance.timestamp DESC"
        
        cur.execute(query, tuple(params))
        records = cur.fetchall()
        
        # If no records are found, display a "not found" message
        if not records:
            not_found = True
        else:
            not_found = False
    else:
        not_found = False
    
    conn.close()
    return render_template('dashboard.html', records=records, names=names, dates=dates, not_found=not_found)

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
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        student_name = request.form.get('student_name')
        # Prefer ID if provided, else use name
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
            # Pie chart data
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
            # Theory attendance dates (status = 'Present' or 'Check-In')
            cur.execute('''
                SELECT DATE(timestamp) FROM attendance
                WHERE user_id=? AND (status='Present' OR status='Check-In')
                ORDER BY timestamp DESC
            ''', (selected_student,))
            attendance_dates = [row[0] for row in cur.fetchall()]
    conn.close()
    return render_template(
        'teacher_dashboard.html',
        students=students,
        graph=graph,
        selected_student=selected_student,
        attendance_dates=attendance_dates
    )
@app.route('/checkin', methods=['GET', 'POST'])
def checkin_attendance():
    if request.method == 'POST':
        known_face_encodings, known_face_names = load_encoded_faces()
        name = recognize_face(known_face_encodings, known_face_names)
        if name:
            mark_attendance(name, status="Check-In")
            return render_template('checkin.html', result=f"{name} checked in successfully!")
        return render_template('checkin.html', result="Face not recognized.")
    return render_template('checkin.html', result=None)



@app.route('/checkout', methods=['GET', 'POST'])
def checkout_attendance():
    if request.method == 'POST':
        known_face_encodings, known_face_names = load_encoded_faces()
        name = recognize_face(known_face_encodings, known_face_names)
        if name:
            mark_attendance(name, status="Check-Out")
            return render_template('checkout.html', result=f"{name} checked out successfully!")
        return render_template('checkout.html', result="Face not recognized.")
    return render_template('checkout.html', result=None)



@app.route('/students')
def show_students():
     if not session.get('logged_in'):
        return redirect(url_for('login'))
        
     conn = sqlite3.connect('database.db')
     cur = conn.cursor()
     cur.execute("SELECT name, student_id, image_path, id FROM users")
     students = cur.fetchall()
     conn.close()
     return render_template('students.html', students=students)

@app.route('/delete_student_by_id', methods=['POST'])
def delete_student_by_id():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    student_id = request.form.get('student_id')

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    # Get image path for deletion
    cur.execute("SELECT image_path FROM users WHERE student_id = ?", (student_id,))
    result = cur.fetchone()

    if result:
        image_path = result[0]
        if image_path and os.path.exists(image_path):
            os.remove(image_path)

        # Delete records
        cur.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
        cur.execute("DELETE FROM users WHERE student_id = ?", (student_id,))
        conn.commit()
        flash(f"✅ Student ID {student_id} deleted successfully.", "success")
    else:
        flash(f"❌ No student found with ID {student_id}.", "danger")
    conn.close()
    return redirect(url_for('show_students'))


def mark_attendance(name, status):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    # Get user ID by name
    cur.execute("SELECT id FROM users WHERE name = ?", (name,))
    user = cur.fetchone()
    if user:
        user_id = user[0]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("INSERT INTO attendance (user_id, timestamp, status) VALUES (?, ?, ?)", (user_id, timestamp, status))
        conn.commit()

    conn.close()

def load_encoded_faces():
    known_encodings = []
    known_names = []

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT name, image_path FROM users")
    users = cur.fetchall()
    conn.close()

    for name, path in users:
        img = face_recognition.load_image_file(path)
        encodings = face_recognition.face_encodings(img)
        if encodings:
            known_encodings.append(encodings[0])
            known_names.append(name)

    return known_encodings, known_names


def recognize_face(known_encodings, known_names, tolerance=0.5):
    cap = cv2.VideoCapture(0)
    success, frame = cap.read()
    cap.release()

    if not success:
        return None

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)

    if not face_locations:
        return None

    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    for encoding in face_encodings:
        distances = face_recognition.face_distance(known_encodings, encoding)
        min_distance = min(distances)
        if min_distance < tolerance:
            best_match_index = distances.tolist().index(min_distance)
            return known_names[best_match_index]
        else:
            print("Face found but not matching any registered user")
            return None

    return None

@app.route('/download_excel')
def download_excel():
    conn = sqlite3.connect('database.db')

    # ✅ Join attendance with users to get all the required info
    df = pd.read_sql_query("""
        SELECT 
            users.name,
            users.student_id,
            users.class_year,
            users.department,
            attendance.timestamp,
            attendance.status
        FROM attendance
        JOIN users ON attendance.user_id = users.id
        ORDER BY attendance.timestamp DESC
    """, conn)

    # ✅ Optional: Split timestamp into Date and Time
    df['Date'] = pd.to_datetime(df['timestamp']).dt.date
    df['Time'] = pd.to_datetime(df['timestamp']).dt.time
    df.drop(columns=['timestamp'], inplace=True)

    conn.close()

    # ✅ Save to Excel
    file_path = 'static/attendance_data.xlsx'
    df.to_excel(file_path, index=False)

    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)

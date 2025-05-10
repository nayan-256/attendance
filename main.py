import os
import cv2
import pickle
import face_recognition
import numpy as np
import sqlite3
import base64
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session

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
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        image_path TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        timestamp TEXT,
        status TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')
    # Insert default admin if not exists
    cur.execute("SELECT * FROM admin WHERE username='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO admin (username, password) VALUES (?, ?)", ('admin', 'admin123'))  # Change this in production
    conn.commit()
    conn.close()

init_db()


@app.route('/')
def home():
    return render_template('index.html')
    
from flask import flash, redirect, render_template, request, session, url_for

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
    return redirect(url_for('home'))

# === Routes ===

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        student_id = request.form['student_id']
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
            cur.execute("INSERT INTO users (name, student_id, image_path) VALUES (?, ?, ?)",
                        (name, student_id, filepath))
            conn.commit()
            conn.close()

            return redirect(url_for('home'))

    # GET or fallback render
    return render_template('register.html')



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
            cur.execute("INSERT INTO attendance (user_id, timestamp) VALUES (?, ?)", (matched_id, timestamp))
            conn.commit()

    conn.close()
    return render_template('attendance.html')
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
            SELECT users.name, 
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
     cur.execute("SELECT name, student_id, image_path FROM users")
     students = cur.fetchall()
     conn.close()
     return render_template('students.html', students=students)

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


if __name__ == '__main__':
    app.run(debug=True)

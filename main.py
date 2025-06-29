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


@app.route('/', endpoint='home')
def home():
    return render_template('index.html')
    

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

    # Get recent attendance (ignore status from DB)
    cur.execute('''
        SELECT DATE(timestamp) AS date, TIME(timestamp) AS time
        FROM attendance
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT 10
    ''', (student['id'],))
    db_records = cur.fetchall()

    # Always set status to "Present"
    attendance_records = []
    for record in db_records:
        attendance_records.append({
            'date': record['date'],
            'time': record['time'],
            'status': 'Present'
        })

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
            return redirect(url_for('student_home'))  # ✅ Redirect to new home screen
        else:
            flash("Invalid credentials", "danger")

    return render_template('student_login.html')

@app.route('/student_home')
def student_home():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    return render_template('student_home.html')


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
            return redirect(url_for('home'))
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
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename).replace('\\','/')

            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

            with open(filepath, 'wb') as f:
                f.write(image_bytes)

            # ✅ Save to database
            cur.execute("INSERT INTO users (name, student_id, class_year,department,password, image_path) VALUES (?, ?, ?, ?,?,?)",
                    (name, student_id, class_year,department,password, filepath))
            conn.commit()
            conn.close()
            # session['student_id'] = student_id   # ✅ Add this line

            return redirect(url_for('home'))

    # GET or fallback render
    return render_template('register.html')

@app.route('/profile')
def profile():
    student_id = session.get('student_id')
    if not student_id:
        flash("Please login first.", "warning")
        return redirect(url_for('student_login'))

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE student_id = ?", (student_id,))
    row = cur.fetchone()
    conn.close()

    if row:
        # Get image path - first try database, then smart matching
        image_path = None
        
        if row['image_path']:
            # Clean up existing database path
            db_image_path = row['image_path'].replace('\\', '/').replace('static/', '')
            if os.path.exists(os.path.join('static', db_image_path)):
                image_path = db_image_path
        
        # If no valid image in database, try smart matching
        if not image_path:
            student_name = row['name']
            image_path = find_student_image(student_name)
        
        # Final fallback to default
        if not image_path or not os.path.exists(os.path.join('static', image_path)):
            image_path = 'default_profile.svg'
        
        user = {
            'name': row['name'],
            'student_id': row['student_id'],
            'class_year': row['class_year'],
            'department': row['department'],
            'image_path': image_path
        }
        return render_template('profile.html', user=user)
    else:
        flash("Student profile not found", "danger")
        return redirect(url_for('student_login'))

def find_student_image(student_name):
    """
    Smart function to find student image from uploads folder
    Matches student name with uploaded image filenames
    """
    import os
    import glob
    
    uploads_dir = os.path.join('static', 'uploads')
    
    if not os.path.exists(uploads_dir):
        return 'default_profile.svg'
    
    # Get all image files from uploads folder
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif']
    image_files = []
    
    for extension in image_extensions:
        image_files.extend(glob.glob(os.path.join(uploads_dir, extension)))
    
    if not image_files:
        return 'default_profile.svg'
    
    # Clean student name for matching
    clean_name = student_name.lower().replace(' ', '_').replace('.', '').strip()
    name_parts = [part.strip() for part in student_name.lower().split() if len(part.strip()) > 1]
    
    # Try different matching strategies
    best_match = None
    max_score = 0
    
    for image_path in image_files:
        image_filename = os.path.basename(image_path).lower()
        score = 0
        
        # Strategy 1: Exact name match
        if clean_name in image_filename:
            score += 15
        
        # Strategy 2: Individual name parts match
        for part in name_parts:
            if len(part) > 2 and part in image_filename:
                score += 5
        
        # Strategy 3: First name + last name combination
        if len(name_parts) >= 2:
            first_last = f"{name_parts[0]}_{name_parts[-1]}"
            if first_last in image_filename:
                score += 12
            
            # Also try without underscore
            first_last_nospace = f"{name_parts[0]}{name_parts[-1]}"
            if first_last_nospace in image_filename:
                score += 10
        
        # Strategy 4: Any name part at the beginning of filename
        for part in name_parts:
            if len(part) > 2 and image_filename.startswith(part):
                score += 8
        
        # Strategy 5: Loose matching for common variations
        if len(name_parts) > 0:
            first_name = name_parts[0]
            if len(first_name) > 3 and first_name in image_filename:
                score += 6
        
        if score > max_score:
            max_score = score
            best_match = image_path
    
    if best_match and max_score > 0:
        # Convert to relative path for web serving
        relative_path = best_match.replace('\\', '/').replace('static/', '')
        return relative_path
    else:
        # Return default profile image if no good match found
        return 'default_profile.svg'

# Helper function to get all available student images for admin
def get_all_student_images():
    """
    Get all student images from uploads folder with metadata
    """
    import os
    import glob
    from datetime import datetime
    
    uploads_dir = os.path.join('static', 'uploads')
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif']
    images = []
    
    for extension in image_extensions:
        for image_path in glob.glob(os.path.join(uploads_dir, extension)):
            filename = os.path.basename(image_path)
            
            # Extract student name from filename (assuming format: name_timestamp.ext)
            name_part = filename.split('_')[0] if '_' in filename else filename.split('.')[0]
            
            # Get file modification time
            mod_time = os.path.getmtime(image_path)
            upload_date = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M')
            
            images.append({
                'filename': filename,
                'path': image_path.replace('\\', '/').replace('static/', ''),
                'student_name': name_part.replace('_', ' ').title(),
                'upload_date': upload_date
            })
    
    return sorted(images, key=lambda x: x['upload_date'], reverse=True)

  
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    student_id = session.get('student_id')
    if not student_id:
        flash("Please log in to edit your profile", "warning")
        return redirect(url_for('student_login'))

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        class_year = request.form['class_year']
        department = request.form['department']
        password = request.form.get('password', '').strip()
        
        # Handle profile image upload
        new_image_path = None
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and file.filename and file.filename != '':
                # Validate file type
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                    # Generate unique filename
                    file_extension = file.filename.rsplit('.', 1)[1].lower()
                    unique_filename = f"{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{str(uuid.uuid4())[:8]}.{file_extension}"
                    
                    # Ensure upload directory exists
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    
                    # Save file
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(filepath)
                    
                    # Store relative path for database
                    new_image_path = f"uploads/{unique_filename}"
                    
                    flash("Profile photo updated successfully!", "success")
                else:
                    flash("Invalid file type. Please upload PNG, JPG, JPEG, or GIF files only.", "error")

        # Prepare update query and parameters
        update_fields = ["name = ?", "class_year = ?", "department = ?"]
        update_params = [name, class_year, department]
        
        # Add image path if new image was uploaded
        if new_image_path:
            update_fields.append("image_path = ?")
            update_params.append(new_image_path)
        
        # Add password if provided
        if password:
            update_fields.append("password = ?")
            update_params.append(password)
        
        # Add student_id for WHERE clause
        update_params.append(student_id)
        
        # Execute update
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE student_id = ?"
        cur.execute(query, update_params)
        
        conn.commit()
        conn.close()
        
        if not new_image_path:  # Only show general success if no image success was shown
            flash("Profile updated successfully!", "success")
        
        return redirect(url_for('profile'))

    # GET: load existing user data with image path
    cur.execute("SELECT * FROM users WHERE student_id = ?", (student_id,))
    user_row = cur.fetchone()
    conn.close()
    
    if user_row:
        # Get current image path
        current_image_path = None
        if user_row['image_path']:
            # Clean up database path
            db_image_path = user_row['image_path'].replace('\\', '/').replace('static/', '')
            if os.path.exists(os.path.join('static', db_image_path)):
                current_image_path = db_image_path
        
        # If no valid image in database, try smart matching
        if not current_image_path:
            current_image_path = find_student_image(user_row['name'])
        
        # Final fallback
        if not current_image_path or not os.path.exists(os.path.join('static', current_image_path)):
            current_image_path = 'default_profile.svg'
        
        user = {
            'name': user_row['name'],
            'student_id': user_row['student_id'],
            'class_year': user_row['class_year'],
            'department': user_row['department'],
            'image_path': current_image_path
        }
        return render_template('edit_profile.html', user=user)
    else:
        flash("User not found", "error")
        return redirect(url_for('student_login'))


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

    # Convert to DataFrame for plotting
    df = pd.DataFrame(records, columns=['name', 'student_id', 'class_year', 'department', 'timestamp'])

    if df.empty:
        weekly_summary = []
        monthly_summary = []
    else:
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Add week and month columns
        df['week'] = df['timestamp'].dt.to_period('W').apply(lambda r: r.start_time.strftime('%Y-%m-%d'))
        df['month'] = df['timestamp'].dt.to_period('M').apply(lambda r: r.start_time.strftime('%Y-%m'))

        # Group by week and month
        weekly_summary = df.groupby('week').size().reset_index(name='count').to_dict(orient='records')
        monthly_summary = df.groupby('month').size().reset_index(name='count').to_dict(orient='records')
        weekly_summary = weekly_summary if weekly_summary is not None else []
        monthly_summary = monthly_summary if monthly_summary is not None else []

    return render_template(
        "dashboard.html",
        records=records,
        weekly_summary=weekly_summary or [],
        monthly_summary=monthly_summary or []
    )

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    # Ensure the user is logged in before proceeding
    if not session.get('logged_in'):
        flash("Please log in as admin to view attendance records", "warning")
        return redirect(url_for('login'))  # Redirect to login page if not logged in
    
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    
    # Fetch all unique names and dates for the dropdowns
    cur.execute('SELECT DISTINCT name FROM users ORDER BY name')
    names = cur.fetchall()
    
    cur.execute('SELECT DISTINCT DATE(timestamp) FROM attendance ORDER BY timestamp DESC')
    dates = cur.fetchall()
    
    # Initialize variables
    records = []
    not_found = False
    show_results = False
    
    if request.method == 'POST':
        show_results = True
        selected_name = request.form.get('name')
        selected_date = request.form.get('date')
        show_all = request.form.get('show_all')
        
        # Query for all attendance records (including historical data)
        # Show all statuses to provide complete attendance history
        query = '''
            SELECT 
                users.name,
                users.student_id,
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
        
        # If show_all button is clicked, don't add additional filters
        if not show_all:
            if selected_name and selected_name != '':
                conditions.append("users.name = ?")
                params.append(selected_name)
            
            if selected_date and selected_date != '':
                conditions.append("DATE(attendance.timestamp) = ?")
                params.append(selected_date)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY attendance.timestamp DESC"
        
        cur.execute(query, tuple(params))
        records = cur.fetchall()
        
        # If no records are found, display a "not found" message
        not_found = len(records) == 0
    
    # For GET request, don't show any records by default
    # Records will only be shown when search is performed
    
    conn.close()
    return render_template('dashboard.html', 
                         records=records, 
                         names=names, 
                         dates=dates, 
                         not_found=not_found,
                         show_results=show_results)

# Direct attendance viewing route (for easier access during testing)
@app.route('/view_all_attendance')
def view_all_attendance():
    """Direct route to view all attendance records"""
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    
    # Get recent attendance records (last 50)
    query = '''
        SELECT 
            users.name,
            users.student_id,
            users.class_year, 
            users.department, 
            DATE(attendance.timestamp) AS date, 
            TIME(attendance.timestamp) AS time, 
            attendance.status 
        FROM attendance 
        JOIN users ON attendance.user_id = users.id
        ORDER BY attendance.timestamp DESC 
        LIMIT 50
    '''
    cur.execute(query)
    records = cur.fetchall()
    
    # Get unique names and dates for filters
    cur.execute('SELECT DISTINCT name FROM users ORDER BY name')
    names = cur.fetchall()
    
    cur.execute('SELECT DISTINCT DATE(timestamp) FROM attendance ORDER BY timestamp DESC LIMIT 30')
    dates = cur.fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         records=records, 
                         names=names, 
                         dates=dates, 
                         not_found=False,
                         show_all=True)

from collections import defaultdict
from datetime import datetime

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
            # Pie chart
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

            # Attendance Dates
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

            # Weekly and Monthly Summary
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
                date = datetime.strptime(date_str, '%Y-%m-%d')
                week_label = f"{date.strftime('%Y')}-W{date.strftime('%U')}"
                month_label = date.strftime('%Y-%m')
                weekly[week_label] += 1
                monthly[month_label] += 1

            weekly_summary = dict(weekly)
            monthly_summary = dict(monthly)

    conn.close()
    # Keep as dictionaries for JavaScript consumption
    # Don't convert to lists of objects
    
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



@app.route('/students', endpoint='show_students')
def show_students():
     if not session.get('logged_in'):
        return redirect(url_for('login'))
        
     conn = sqlite3.connect('database.db')
     conn.row_factory = sqlite3.Row
     cur = conn.cursor()
     cur.execute("SELECT * FROM users ORDER BY name")
     users = cur.fetchall()
     conn.close()
     
     # Enhanced students data with profile images
     students_data = []
     for user in users:
         # Get image path - first try database, then smart matching
         image_path = None
         
         if user['image_path']:
             # Clean up existing database path
             db_image_path = user['image_path'].replace('\\', '/').replace('static/', '')
             if os.path.exists(os.path.join('static', db_image_path)):
                 image_path = db_image_path
         
         # If no valid image in database, try smart matching
         if not image_path:
             student_name = user['name']
             image_path = find_student_image(student_name)
         
         # Final fallback to default
         if not image_path or not os.path.exists(os.path.join('static', image_path)):
             image_path = 'default_profile.svg'
         
         student_data = {
             'id': user['id'],
             'name': user['name'],
             'student_id': user['student_id'],
             'class_year': user['class_year'],
             'department': user['department'],
             'image_path': image_path,
             'db_image_path': user['image_path']
         }
         students_data.append(student_data)
     
     return render_template('students.html', students=students_data)

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
@app.route("/chatbot")
def chatbot_page():
    return render_template("chatbot.html")

# Chatbot response API (handles user messages)
@app.route('/chatbot', methods=['POST'])
def chatbot_response():
    user_input = request.json.get('message', '').lower()

    if "how many classes" in user_input:
        return jsonify({'response': "You missed 3 classes this week."})
    elif "how do i request leave" in user_input:
        return jsonify({'response': "Go to your dashboard > Leave Request."})
    else:
        return jsonify({'response': "I'm not sure. Please try asking about attendance or leave."})


print(app.url_map)

if __name__ == '__main__':
    app.run(debug=True)
@app.route('/api/holidays/<int:year>')
def get_holidays(year):
    """API endpoint to get holidays for a specific year"""
    # Static holiday data - can be moved to database later
    holidays_data = {
        2025: [
            {'date': '2025-01-01', 'name': 'New Year\'s Day', 'reason': 'National Holiday', 'type': 'national'},
            {'date': '2025-01-26', 'name': 'Republic Day', 'reason': 'National Holiday', 'type': 'national'},
            {'date': '2025-03-14', 'name': 'Holi', 'reason': 'Festival of Colors', 'type': 'festival'},
            {'date': '2025-04-14', 'name': 'Good Friday', 'reason': 'Christian Holiday', 'type': 'religious'},
            {'date': '2025-04-18', 'name': 'Ram Navami', 'reason': 'Hindu Festival', 'type': 'religious'},
            {'date': '2025-05-01', 'name': 'Labour Day', 'reason': 'International Workers\' Day', 'type': 'national'},
            {'date': '2025-08-15', 'name': 'Independence Day', 'reason': 'National Holiday', 'type': 'national'},
            {'date': '2025-08-29', 'name': 'Janmashtami', 'reason': 'Hindu Festival', 'type': 'religious'},
            {'date': '2025-10-02', 'name': 'Gandhi Jayanti', 'reason': 'National Holiday', 'type': 'national'},
            {'date': '2025-10-31', 'name': 'Diwali', 'reason': 'Festival of Lights', 'type': 'festival'},
            {'date': '2025-12-25', 'name': 'Christmas Day', 'reason': 'Christian Holiday', 'type': 'religious'}
        ],
        2024: [
            {'date': '2024-01-01', 'name': 'New Year\'s Day', 'reason': 'National Holiday', 'type': 'national'},
            {'date': '2024-01-26', 'name': 'Republic Day', 'reason': 'National Holiday', 'type': 'national'},
            {'date': '2024-03-25', 'name': 'Holi', 'reason': 'Festival of Colors', 'type': 'festival'},
            {'date': '2024-03-29', 'name': 'Good Friday', 'reason': 'Christian Holiday', 'type': 'religious'},
            {'date': '2024-04-17', 'name': 'Ram Navami', 'reason': 'Hindu Festival', 'type': 'religious'},
            {'date': '2024-05-01', 'name': 'Labour Day', 'reason': 'International Workers\' Day', 'type': 'national'},
            {'date': '2024-08-15', 'name': 'Independence Day', 'reason': 'National Holiday', 'type': 'national'},
            {'date': '2024-08-26', 'name': 'Janmashtami', 'reason': 'Hindu Festival', 'type': 'religious'},
            {'date': '2024-10-02', 'name': 'Gandhi Jayanti', 'reason': 'National Holiday', 'type': 'national'},
            {'date': '2024-11-01', 'name': 'Diwali', 'reason': 'Festival of Lights', 'type': 'festival'},
            {'date': '2024-12-25', 'name': 'Christmas Day', 'reason': 'Christian Holiday', 'type': 'religious'}
        ],
        2026: [
            {'date': '2026-01-01', 'name': 'New Year\'s Day', 'reason': 'National Holiday', 'type': 'national'},
            {'date': '2026-01-26', 'name': 'Republic Day', 'reason': 'National Holiday', 'type': 'national'},
            {'date': '2026-03-05', 'name': 'Holi', 'reason': 'Festival of Colors', 'type': 'festival'},
            {'date': '2026-04-03', 'name': 'Good Friday', 'reason': 'Christian Holiday', 'type': 'religious'},
            {'date': '2026-04-06', 'name': 'Ram Navami', 'reason': 'Hindu Festival', 'type': 'religious'},
            {'date': '2026-05-01', 'name': 'Labour Day', 'reason': 'International Workers\' Day', 'type': 'national'},
            {'date': '2026-08-15', 'name': 'Independence Day', 'reason': 'National Holiday', 'type': 'national'},
            {'date': '2026-08-17', 'name': 'Janmashtami', 'reason': 'Hindu Festival', 'type': 'religious'},
            {'date': '2026-10-02', 'name': 'Gandhi Jayanti', 'reason': 'National Holiday', 'type': 'national'},
            {'date': '2026-10-19', 'name': 'Diwali', 'reason': 'Festival of Lights', 'type': 'festival'},
            {'date': '2026-12-25', 'name': 'Christmas Day', 'reason': 'Christian Holiday', 'type': 'religious'}
        ]
    }
    
    from flask import jsonify
    return jsonify(holidays_data.get(year, []))


# Admin route to view all students with their images - DISABLED to avoid endpoint conflicts
# @app.route('/admin/students', endpoint='admin_students_view')
# def admin_students():
#     """Admin route to view all registered students with their profile images"""
#     conn = sqlite3.connect('database.db')
#     conn.row_factory = sqlite3.Row
#     cur = conn.cursor()
#     cur.execute("SELECT * FROM users ORDER BY name")
#     users = cur.fetchall()
#     conn.close()
#     
#     students_data = []
#     for user in users:
#         # Get image path - first try database, then smart matching
#         image_path = None
#         
#         if user['image_path']:
#             # Clean up existing database path
#             db_image_path = user['image_path'].replace('\\', '/').replace('static/', '')
#             if os.path.exists(os.path.join('static', db_image_path)):
#                 image_path = db_image_path
#         
#         # If no valid image in database, try smart matching
#         if not image_path:
#             student_name = user['name']
#             image_path = find_student_image(student_name)
#         
#         # Final fallback to default
#         if not image_path or not os.path.exists(os.path.join('static', image_path)):
#             image_path = 'default_profile.svg'
#         
#         student_data = {
#             'name': user['name'],
#             'student_id': user['student_id'],
#             'class_year': user['class_year'],
#             'department': user['department'],
#             'image_path': image_path,
#             'db_image_path': user['image_path'],
#             'image_exists': os.path.exists(os.path.join('static', image_path))
#         }
#         students_data.append(student_data)
#     
#     return render_template('admin_students.html', students=students_data)

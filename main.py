import os
import glob
# import cv2
# import pickle
# import face_recognition
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
import random
import logging
from datetime import datetime,timedelta
from collections import defaultdict
from flask import Flask, flash, send_file, render_template, request, redirect, url_for, session,jsonify
from werkzeug.utils import secure_filename

# Optional imports that might cause issues
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    print("Warning: OpenCV (cv2) not available")
    CV2_AVAILABLE = False

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    print("Warning: face_recognition not available")
    FACE_RECOGNITION_AVAILABLE = False


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['RESOURCES_FOLDER'] = 'static/resources'
app.secret_key = '123'

# Create upload and resources folders if they don't exist
try:
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['RESOURCES_FOLDER']):
        os.makedirs(app.config['RESOURCES_FOLDER'])
except Exception as e:
    logging.error(f"Error creating directories: {str(e)}")

# File upload settings
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt', 'jpg', 'jpeg', 'png', 'zip', 'rar'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Performance optimizations
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # Cache static files for 1 year
app.config['JSON_SORT_KEYS'] = False  # Don't sort JSON keys (faster)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False  # Compact JSON (faster)

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

    # Create subjects table
    cur.execute('''CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_name TEXT UNIQUE,
        subject_code TEXT UNIQUE,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Insert default subjects
    default_subjects = [
        ('Data Structures and Algorithms (Computer)', 'DSA101', 'Data Structures and Algorithms for Computer Engineering'),
        ('Electrical Machines (Electrical)', 'EM101', 'Electrical Machines for Electrical Engineering'),
        ('Communication Systems (ENTC)', 'CS201', 'Communication Systems for Electronics and Telecommunication'),
        ('Theory of Machines (Mechanical)', 'TOM101', 'Theory of Machines for Mechanical Engineering'),
        ('Structural Analysis (Civil)', 'SA101', 'Structural Analysis for Civil Engineering'),
        ('Process Control (Instrumentation)', 'PC101', 'Process Control for Instrumentation Engineering'),
        ('Computer Networks (Computer)', 'CN101', 'Computer Networks for Computer Engineering'),
        ('Power Systems (Electrical)', 'PS101', 'Power Systems for Electrical Engineering'),
        ('Concrete Technology (Civil)', 'CT101', 'Concrete Technology for Civil Engineering'),
        ('Microcontrollers and Applications (ENTC / Instrumentation)', 'MCA101', 'Microcontrollers and Applications for ENTC and Instrumentation')
    ]
    
    for subject_name, subject_code, description in default_subjects:
        cur.execute("SELECT * FROM subjects WHERE subject_code=?", (subject_code,))
        if not cur.fetchone():
            cur.execute("INSERT INTO subjects (subject_name, subject_code, description) VALUES (?, ?, ?)", 
                       (subject_name, subject_code, description))

    # Create teacher_subjects mapping table
    cur.execute('''CREATE TABLE IF NOT EXISTS teacher_subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id INTEGER,
        subject_id INTEGER,
        FOREIGN KEY(teacher_id) REFERENCES teachers(id),
        FOREIGN KEY(subject_id) REFERENCES subjects(id),
        UNIQUE(teacher_id, subject_id)
    )''')

    # Add default teacher-subject mappings
    cur.execute("SELECT id FROM teachers WHERE username='teacher1'")
    teacher_result = cur.fetchone()
    if teacher_result:
        teacher_id = teacher_result[0]
        # Assign first 3 subjects to teacher1 for demo
        for i in range(1, 4):
            cur.execute("""
                INSERT OR IGNORE INTO teacher_subjects (teacher_id, subject_id) 
                VALUES (?, ?)
            """, (teacher_id, i))

    # Create resources table for file uploads
    cur.execute('''CREATE TABLE IF NOT EXISTS resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        file_path TEXT NOT NULL,
        original_filename TEXT NOT NULL,
        file_size INTEGER,
        file_type TEXT,
        subject_id INTEGER,
        teacher_id INTEGER,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY(subject_id) REFERENCES subjects(id),
        FOREIGN KEY(teacher_id) REFERENCES teachers(id)
    )''')

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
    if not FACE_RECOGNITION_AVAILABLE or not CV2_AVAILABLE:
        flash("Face recognition or camera functionality is not available on this system.", "warning")
        return render_template('attendance.html', error="Face recognition not available")
    
    known_encodings = []
    known_ids = []

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT id, image_path FROM users")
    users = cur.fetchall()

    try:
        for user in users:
            if user[1] and os.path.exists(user[1]):
                img = face_recognition.load_image_file(user[1])
                encodings = face_recognition.face_encodings(img)
                if encodings:
                    known_encodings.append(encodings[0])
                    known_ids.append(user[0])

        cap = cv2.VideoCapture(0)
        success, frame = cap.read()
        cap.release()

        if success:
            face_locations = face_recognition.face_locations(frame)
            face_encodings = face_recognition.face_encodings(frame, face_locations)

            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(known_encodings, face_encoding)
                if True in matches:
                    matched_id = known_ids[matches.index(True)]
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cur.execute("INSERT INTO attendance (user_id, timestamp, status) VALUES (?, ?, ?)", (matched_id, timestamp, "Present"))
                    conn.commit()
                    flash("Attendance marked successfully!", "success")
                    break
            else:
                flash("No recognized face found", "warning")
        else:
            flash("Camera not accessible", "error")
            
    except Exception as e:
        flash(f"Error during face recognition: {str(e)}", "error")
        
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
@app.route('/teacher_resources')
def teacher_resources():
    if not session.get('teacher_logged_in'):
        return redirect(url_for('teacher_login'))
    
    try:
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        
        # Get teacher's subjects
        teacher_username = session.get('teacher_username')
        cur.execute('SELECT id FROM teachers WHERE username=?', (teacher_username,))
        teacher_result = cur.fetchone()
        
        if teacher_result:
            teacher_id = teacher_result[0]
            
            # Get subjects assigned to this teacher
            cur.execute('''
                SELECT s.id, s.subject_name, s.subject_code 
                FROM subjects s 
                JOIN teacher_subjects ts ON s.id = ts.subject_id 
                WHERE ts.teacher_id = ?
            ''', (teacher_id,))
            subjects = cur.fetchall()
            
            # Get resources uploaded by this teacher
            cur.execute('''
                SELECT r.id, r.title, r.description, r.original_filename, 
                       r.file_size, r.upload_date, s.subject_name, s.subject_code
                FROM resources r 
                JOIN subjects s ON r.subject_id = s.id 
                WHERE r.teacher_id = ? AND r.is_active = 1
                ORDER BY r.upload_date DESC
            ''', (teacher_id,))
            resources = cur.fetchall()
        else:
            subjects = []
            resources = []
        
        conn.close()
        return render_template('teacher_resources.html', subjects=subjects, resources=resources)
        
    except Exception as e:
        logging.error(f"Error in teacher_resources: {str(e)}")
        flash('Error loading teacher resources. Please try again.', 'error')
        return redirect(url_for('home'))

@app.route('/upload_resource', methods=['POST'])
def upload_resource():
    if not session.get('teacher_logged_in'):
        return redirect(url_for('teacher_login'))
    
    try:
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('teacher_resources'))
        
        file = request.files['file']
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        subject_id = request.form.get('subject_id')
        
        if file.filename == '' or not title or not subject_id:
            flash('Please fill all required fields', 'error')
            return redirect(url_for('teacher_resources'))
        
        if file and allowed_file(file.filename):
            # Create unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{secure_filename(file.filename)}"
            file_path = os.path.join(app.config['RESOURCES_FOLDER'], filename)
            
            # Ensure resources directory exists
            os.makedirs(app.config['RESOURCES_FOLDER'], exist_ok=True)
            
            file.save(file_path)
            file_size = os.path.getsize(file_path)
            file_type = file.filename.rsplit('.', 1)[1].lower()
            
            # Get teacher ID
            conn = sqlite3.connect('database.db')
            cur = conn.cursor()
            teacher_username = session.get('teacher_username')
            cur.execute('SELECT id FROM teachers WHERE username=?', (teacher_username,))
            teacher_result = cur.fetchone()
            
            if teacher_result:
                teacher_id = teacher_result[0]
                
                # Insert resource record
                cur.execute('''
                    INSERT INTO resources (title, description, file_path, original_filename, 
                                         file_size, file_type, subject_id, teacher_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (title, description, file_path, file.filename, file_size, file_type, subject_id, teacher_id))
                
                conn.commit()
                flash('Resource uploaded successfully!', 'success')
            else:
                flash('Error: Teacher not found', 'error')
            
            conn.close()
            
        else:
            flash('Invalid file type. Allowed types: PDF, DOC, DOCX, PPT, PPTX, TXT, JPG, PNG, ZIP, RAR', 'error')
    
    except Exception as e:
        logging.error(f"Error in upload_resource: {str(e)}")
        flash(f'Error uploading file: {str(e)}', 'error')
    
    return redirect(url_for('teacher_resources'))

@app.route('/delete_resource/<int:resource_id>')
def delete_resource(resource_id):
    if not session.get('teacher_logged_in'):
        return redirect(url_for('teacher_login'))
    
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    
    # Get teacher ID
    teacher_username = session.get('teacher_username')
    cur.execute('SELECT id FROM teachers WHERE username=?', (teacher_username,))
    teacher_result = cur.fetchone()
    
    if teacher_result:
        teacher_id = teacher_result[0]
        
        # Check if resource belongs to this teacher and get file path
        cur.execute('SELECT file_path FROM resources WHERE id=? AND teacher_id=?', (resource_id, teacher_id))
        resource = cur.fetchone()
        
        if resource:
            file_path = resource[0]
            
            # Delete file from filesystem
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error deleting file: {e}")
            
            # Mark resource as inactive in database
            cur.execute('UPDATE resources SET is_active=0 WHERE id=?', (resource_id,))
            conn.commit()
            flash('Resource deleted successfully!')
        else:
            flash('Resource not found or unauthorized')
    
    conn.close()
    return redirect(url_for('teacher_resources'))

@app.route('/student_resources')
def student_resources():
    if not session.get('student_id'):
        return redirect(url_for('student_login'))
    
    try:
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        
        # Get all available resources grouped by subject
        cur.execute('''
            SELECT r.id, r.title, r.description, r.original_filename, 
                   r.file_size, r.upload_date, s.subject_name, s.subject_code,
                   t.username as teacher_name
            FROM resources r 
            JOIN subjects s ON r.subject_id = s.id 
            JOIN teachers t ON r.teacher_id = t.id
            WHERE r.is_active = 1
            ORDER BY s.subject_name, r.upload_date DESC
        ''')
        resources = cur.fetchall()
        
        # Group resources by subject
        resources_by_subject = {}
        for resource in resources:
            subject_name = resource[6]  # subject_name is at index 6
            if subject_name not in resources_by_subject:
                resources_by_subject[subject_name] = []
            resources_by_subject[subject_name].append(resource)
        
        conn.close()
        return render_template('student_resources.html', resources_by_subject=resources_by_subject)
    
    except Exception as e:
        logging.error(f"Error in student_resources: {str(e)}")
        flash('Error loading resources. Please try again.', 'error')
        return redirect(url_for('student_home'))

@app.route('/download_resource/<int:resource_id>')
def download_resource(resource_id):
    if not session.get('student_id'):
        return redirect(url_for('student_login'))
    
    try:
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        
        # Get resource details
        cur.execute('''
            SELECT file_path, original_filename 
            FROM resources 
            WHERE id=? AND is_active=1
        ''', (resource_id,))
        resource = cur.fetchone()
        
        conn.close()
        
        if resource and len(resource) >= 2 and os.path.exists(resource[0]):
            return send_file(resource[0], as_attachment=True, download_name=resource[1])
        else:
            flash('File not found or has been removed.', 'error')
            return redirect(url_for('student_resources'))
            
    except Exception as e:
        logging.error(f"Error in download_resource: {str(e)}")
        flash('Error downloading file. Please try again.', 'error')
        return redirect(url_for('student_resources'))

@app.route('/checkin', methods=['GET', 'POST'])
def checkin_attendance():
    if request.method == 'POST':
        if not FACE_RECOGNITION_AVAILABLE or not CV2_AVAILABLE:
            return render_template('checkin.html', result="Face recognition not available on this system.")
        
        try:
            known_face_encodings, known_face_names = load_encoded_faces()
            name = recognize_face(known_face_encodings, known_face_names)
            if name:
                mark_attendance(name, status="Check-In")
                return render_template('checkin.html', result=f"{name} checked in successfully!")
            return render_template('checkin.html', result="Face not recognized.")
        except Exception as e:
            return render_template('checkin.html', result=f"Error: {str(e)}")
    return render_template('checkin.html', result=None)



@app.route('/checkout', methods=['GET', 'POST'])
def checkout_attendance():
    if request.method == 'POST':
        if not FACE_RECOGNITION_AVAILABLE or not CV2_AVAILABLE:
            return render_template('checkout.html', result="Face recognition not available on this system.")
        
        try:
            known_face_encodings, known_face_names = load_encoded_faces()
            name = recognize_face(known_face_encodings, known_face_names)
            if name:
                mark_attendance(name, status="Check-Out")
                return render_template('checkout.html', result=f"{name} checked out successfully!")
            return render_template('checkout.html', result="Face not recognized.")
        except Exception as e:
            return render_template('checkout.html', result=f"Error: {str(e)}")
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
    if not FACE_RECOGNITION_AVAILABLE:
        return [], []
        
    known_encodings = []
    known_names = []

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT name, image_path FROM users")
    users = cur.fetchall()
    conn.close()

    for name, path in users:
        try:
            if path and os.path.exists(path):
                img = face_recognition.load_image_file(path)
                encodings = face_recognition.face_encodings(img)
                if encodings:
                    known_encodings.append(encodings[0])
                    known_names.append(name)
        except Exception as e:
            print(f"Error loading face for {name}: {e}")
            continue

    return known_encodings, known_names


def recognize_face(known_encodings, known_names, tolerance=0.5):
    if not CV2_AVAILABLE or not FACE_RECOGNITION_AVAILABLE:
        return None
        
    try:
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
    except Exception as e:
        print(f"Error in face recognition: {e}")
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

# Enhanced Role-Based Chatbot response API (handles user messages)
@app.route('/chatbot', methods=['POST'])
def chatbot_response():
    user_input = request.json.get('message', '').lower()
    
    # Determine user role and get user info
    user_role = "guest"
    user_info = None
    student_id = session.get('student_id')
    admin_logged_in = session.get('logged_in')
    teacher_logged_in = session.get('teacher_logged_in')
    teacher_username = session.get('teacher_username')
    
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Identify user role and get user info
        if student_id:
            user_role = "student"
            cur.execute("SELECT * FROM users WHERE student_id = ?", (student_id,))
            user_info = cur.fetchone()
        elif admin_logged_in:
            user_role = "admin"
            user_info = {"username": "admin"}
        elif teacher_logged_in:
            user_role = "teacher"
            user_info = {"username": teacher_username}
        
        # Personalized greetings based on role
        if any(word in user_input for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            if user_role == "student" and user_info:
                return jsonify({'response': f"Hello {user_info['name']}! 👋 I'm your attendance assistant. How can I help you today? I can check your attendance, help with leave requests, or answer any questions!"})
            elif user_role == "teacher":
                return jsonify({'response': f"Welcome {teacher_username}! 👋 I'm here to assist you with student attendance management, class statistics, and administrative tasks. How can I help?"})
            elif user_role == "admin":
                return jsonify({'response': "Hello Admin! 👋 I'm your administrative assistant. I can help with system management, student records, attendance reports, and analytics. What would you like to do?"})
            else:
                return jsonify({'response': "Hello! 👋 I'm the attendance assistant. Please log in as a student, teacher, or admin to get personalized help, or ask general questions about the system!"})
        
        elif any(word in user_input for word in ['thanks', 'thank you', 'bye', 'goodbye']):
            return jsonify({'response': "You're welcome! 😊 Feel free to reach out anytime for assistance. Have a great day!"})
        
        # STUDENT-SPECIFIC QUERIES
        if user_role == "student":
            # Student attendance queries
            if "attendance" in user_input and ("my" in user_input or "percentage" in user_input):
                cur.execute("""
                    SELECT COUNT(*) as total_days,
                           SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_days
                    FROM attendance WHERE user_id = ?
                """, (user_info['id'],))
                result = cur.fetchone()
                if result and result['total_days'] > 0:
                    percentage = (result['present_days'] / result['total_days']) * 100
                    status_emoji = "🎉" if percentage >= 75 else "📈" if percentage >= 60 else "⚠️"
                    return jsonify({'response': f"📊 Your attendance: {result['present_days']}/{result['total_days']} days ({percentage:.1f}%) {status_emoji}\n\n{'Excellent attendance!' if percentage >= 75 else 'Good, but try to improve!' if percentage >= 60 else 'You need to attend more classes!'}"})
                else:
                    return jsonify({'response': "📊 No attendance records found yet. Start attending classes to build your record!"})
            
            elif "classes" in user_input and ("missed" in user_input or "absent" in user_input):
                cur.execute("""
                    SELECT COUNT(*) as missed_classes
                    FROM attendance 
                    WHERE user_id = ? AND status = 'Absent'
                """, (user_info['id'],))
                result = cur.fetchone()
                missed = result['missed_classes'] if result else 0
                return jsonify({'response': f"📉 You've missed {missed} classes. {'Try to attend regularly to maintain good attendance!' if missed > 3 else 'Great job maintaining regular attendance! 👍'}"})
            
            elif "today" in user_input and "attendance" in user_input:
                from datetime import date
                today = date.today().isoformat()
                cur.execute("""
                    SELECT status FROM attendance 
                    WHERE user_id = ? AND date(timestamp) = ?
                """, (user_info['id'], today))
                result = cur.fetchone()
                if result:
                    status = result['status']
                    return jsonify({'response': f"📅 Today's attendance: {status} {'✅' if status == 'Present' else '❌'}"})
                else:
                    return jsonify({'response': "📅 No attendance marked for today yet. Don't forget to check in!"})
            
            elif "profile" in user_input or "my info" in user_input:
                return jsonify({'response': f"👤 Your Profile:\n• Name: {user_info['name']}\n• Student ID: {user_info['student_id']}\n• Class: {user_info['class_year']}\n• Department: {user_info['department']}\n\nYou can edit your profile from the student dashboard!"})
            
            elif "leave" in user_input or "absence" in user_input:
                return jsonify({'response': "📝 Leave Application Process:\n1. Go to Student Dashboard\n2. Click 'Apply for Leave'\n3. Fill in dates and reason\n4. Submit for teacher approval\n5. Check status in your dashboard\n\nNeed help with a specific step?"})
        
        # TEACHER-SPECIFIC QUERIES
        elif user_role == "teacher":
            if "class" in user_input and ("average" in user_input or "overall" in user_input or "statistics" in user_input):
                cur.execute("""
                    SELECT 
                        COUNT(DISTINCT user_id) as total_students,
                        AVG(CASE WHEN status = 'Present' THEN 1.0 ELSE 0.0 END) * 100 as avg_attendance,
                        COUNT(*) as total_records
                    FROM attendance
                """)
                result = cur.fetchone()
                if result and result['total_students'] > 0:
                    avg_att = result['avg_attendance']
                    return jsonify({'response': f"📈 Class Statistics:\n• Total Students: {result['total_students']}\n• Average Attendance: {avg_att:.1f}%\n• Total Records: {result['total_records']}\n\nUse Teacher Dashboard for detailed student-wise analysis!"})
                else:
                    return jsonify({'response': "📊 No attendance data available yet."})
            
            elif "student" in user_input and ("list" in user_input or "all" in user_input):
                cur.execute("SELECT name, student_id, class_year FROM users ORDER BY name LIMIT 10")
                students = cur.fetchall()
                if students:
                    student_list = "\n".join([f"• {s['name']} ({s['student_id']}) - {s['class_year']}" for s in students])
                    return jsonify({'response': f"👥 Recent Students:\n{student_list}\n\n{'...(showing first 10)' if len(students) == 10 else ''}\nUse Teacher Dashboard for complete management!"})
                else:
                    return jsonify({'response': "👥 No students registered yet."})
            
            elif "attendance" in user_input and ("mark" in user_input or "record" in user_input):
                return jsonify({'response': "📝 Attendance Management:\n• Use Teacher Dashboard for detailed student analytics\n• View attendance patterns and generate reports\n• Monitor individual student performance\n• Export attendance data to Excel\n\nAccess these features from your teacher dashboard!"})
            
            elif "dashboard" in user_input or "analytics" in user_input:
                return jsonify({'response': "📊 Teacher Dashboard Features:\n• Student-wise attendance analysis\n• Graphical attendance reports\n• Date range filtering\n• Weekly/Monthly summaries\n• Export functionality\n\nNavigate to Teacher Dashboard to access all tools!"})
        
        # ADMIN-SPECIFIC QUERIES
        elif user_role == "admin":
            if "system" in user_input and ("status" in user_input or "overview" in user_input):
                cur.execute("SELECT COUNT(*) as total_students FROM users")
                students_count = cur.fetchone()['total_students']
                cur.execute("SELECT COUNT(*) as total_records FROM attendance")
                records_count = cur.fetchone()['total_records']
                cur.execute("SELECT COUNT(*) as teachers_count FROM teachers")
                teachers_count = cur.fetchone()['teachers_count']
                
                return jsonify({'response': f"🖥️ System Overview:\n• Total Students: {students_count}\n• Total Teachers: {teachers_count}\n• Attendance Records: {records_count}\n• System Status: ✅ Active\n\nUse Admin Dashboard for detailed management!"})
            
            elif "students" in user_input and ("manage" in user_input or "add" in user_input or "delete" in user_input):
                return jsonify({'response': "👥 Student Management:\n• View all registered students\n• Add new student records\n• Delete student accounts\n• Manage student profiles\n• Export student data\n\nAccess these features from the Admin Dashboard!"})
            
            elif "reports" in user_input or "analytics" in user_input:
                return jsonify({'response': "📊 Admin Reports & Analytics:\n• Comprehensive attendance reports\n• Student performance analytics\n• Class-wise statistics\n• Export to Excel/CSV\n• Custom date range reports\n\nGenerate detailed reports from Admin Dashboard!"})
            
            elif "backup" in user_input or "export" in user_input:
                return jsonify({'response': "💾 Data Management:\n• Export attendance data to Excel\n• Backup student records\n• Download comprehensive reports\n• Schedule automated backups\n\nUse the export features in Admin Dashboard!"})
        
        # GENERAL QUERIES (for all users)
        elif "how to" in user_input and ("mark" in user_input or "attendance" in user_input):
            if user_role == "student":
                return jsonify({'response': "📸 Marking Your Attendance:\n1. Go to Check-in page\n2. Position your face clearly in camera\n3. Wait for face recognition\n4. Attendance marked automatically!\n\nTips: Good lighting, face the camera, remove glasses if needed."})
            else:
                return jsonify({'response': "📸 Attendance Marking Process:\n• Students use face recognition system\n• Automatic attendance recording\n• Real-time database updates\n• Manual override available for admins\n\nEnsure proper lighting and camera access!"})
        
        elif "features" in user_input or "what can you do" in user_input:
            if user_role == "student":
                return jsonify({'response': "🤖 I can help you with:\n• Check your attendance percentage\n• View missed classes\n• Profile information\n• Leave application guidance\n• Attendance marking help\n• General queries\n\nJust ask naturally!"})
            elif user_role == "teacher":
                return jsonify({'response': "🤖 Teacher Assistant Features:\n• Class attendance statistics\n• Student performance analytics\n• Attendance reports\n• Dashboard navigation help\n• Data export guidance\n• System management tips"})
            elif user_role == "admin":
                return jsonify({'response': "🤖 Admin Assistant Features:\n• System overview and status\n• Student management guidance\n• Comprehensive reports\n• Data backup and export\n• User account management\n• System analytics"})
            else:
                return jsonify({'response': "🤖 General Features:\n• Role-based assistance\n• Attendance system help\n• Navigation guidance\n• Technical support\n\nPlease log in for personalized assistance!"})
        
        elif "help" in user_input:
            role_specific_help = {
                "student": "• 'What's my attendance?'\n• 'How many classes missed?'\n• 'How to apply for leave?'\n• 'My profile info'",
                "teacher": "• 'Class attendance statistics'\n• 'Show all students'\n• 'How to use dashboard?'\n• 'Generate reports'",
                "admin": "• 'System overview'\n• 'Manage students'\n• 'Generate reports'\n• 'Export data'",
                "guest": "• 'How to mark attendance?'\n• 'System features'\n• Please log in for personalized help"
            }
            return jsonify({'response': f"💡 {user_role.title()} Help:\n{role_specific_help[user_role]}\n\nFeel free to ask in your own words!"})
        
        # Technical issues
        elif "problem" in user_input or "issue" in user_input or "error" in user_input:
            return jsonify({'response': "🔧 Technical Support:\n1. Refresh the page\n2. Clear browser cache\n3. Check internet connection\n4. For face recognition: ensure good lighting\n5. Try different browser\n6. Contact system administrator\n\nDescribe your specific issue for better help!"})
        
        elif "camera" in user_input or "face recognition" in user_input:
            return jsonify({'response': "📸 Face Recognition Help:\n• Ensure good lighting\n• Face camera directly\n• Remove glasses/masks temporarily\n• Stay still during scan\n• Make sure face is registered\n• Check camera permissions\n\nStill having issues? Contact admin for support."})
        
        # Login guidance for guests
        elif user_role == "guest" and any(word in user_input for word in ['login', 'access', 'account']):
            return jsonify({'response': "🔐 Login Options:\n• Student Login: Use your Student ID and password\n• Teacher Login: Use teacher credentials\n• Admin Login: Administrative access\n\nChoose your role from the home page to get started!"})
        
        # Fallback with role-specific suggestions
        else:
            suggestions = {
                "student": ["'What's my attendance percentage?'", "'How to apply for leave?'", "'Show my profile'"],
                "teacher": ["'Class attendance statistics'", "'Show student list'", "'How to use dashboard?'"],
                "admin": ["'System overview'", "'Manage students'", "'Generate reports'"],
                "guest": ["'How to mark attendance?'", "'Login help'", "'System features'"]
            }
            suggestion = random.choice(suggestions[user_role])
            return jsonify({'response': f"🤔 I'm not sure about that. Try asking: {suggestion}\n\nOr type 'help' to see what I can do for {user_role}s!"})
            
    except Exception as e:
        return jsonify({'response': "⚠️ Sorry, I encountered an error. Please try again or contact support if the issue persists."})
    finally:
        if 'conn' in locals():
            conn.close()

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
    
    return jsonify(holidays_data.get(year, []))

@app.route('/api/user-role')
def get_user_role():
    """API endpoint to get current user's role and information for chatbot"""
    try:
        # Check user role and get user info
        student_id = session.get('student_id')
        admin_logged_in = session.get('logged_in')
        teacher_logged_in = session.get('teacher_logged_in')
        teacher_username = session.get('teacher_username')
        
        if student_id:
            # Student user
            conn = sqlite3.connect('database.db')
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT name, student_id, class_year, department FROM users WHERE student_id = ?", (student_id,))
            user_info = cur.fetchone()
            conn.close()
            
            if user_info:
                return jsonify({
                    'role': 'student',
                    'userInfo': {
                        'name': user_info['name'],
                        'student_id': user_info['student_id'],
                        'class_year': user_info['class_year'],
                        'department': user_info['department']
                    }
                })
        elif admin_logged_in:
            # Admin user
            return jsonify({
                'role': 'admin',
                'userInfo': {
                    'username': 'admin'
                }
            })
        elif teacher_logged_in:
            # Teacher user
            return jsonify({
                'role': 'teacher',
                'userInfo': {
                    'username': teacher_username
                }
            })
        
        # Guest user (not logged in)
        return jsonify({
            'role': 'guest',
            'userInfo': None
        })
        
    except Exception as e:
        return jsonify({
            'role': 'guest',
            'userInfo': None,
            'error': str(e)
        })

@app.route('/manage_teachers')
def manage_teachers():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Get all teachers with their subjects
    cur.execute('''
        SELECT t.id, t.username, 
               GROUP_CONCAT(s.subject_name) as subjects
        FROM teachers t
        LEFT JOIN teacher_subjects ts ON t.id = ts.teacher_id
        LEFT JOIN subjects s ON ts.subject_id = s.id
        GROUP BY t.id, t.username
    ''')
    teachers = cur.fetchall()
    
    # Get all subjects for assignment
    cur.execute('SELECT * FROM subjects ORDER BY subject_name')
    subjects = cur.fetchall()
    
    conn.close()
    return render_template('manage_teachers.html', teachers=teachers, subjects=subjects)

@app.route('/add_teacher', methods=['POST'])
def add_teacher():
    username = request.form['username']
    password = request.form['password']
    subject_ids = request.form.getlist('subjects')
    
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    
    try:
        # Add teacher
        cur.execute("INSERT INTO teachers (username, password) VALUES (?, ?)", (username, password))
        teacher_id = cur.lastrowid
        
        # Assign subjects to teacher
        for subject_id in subject_ids:
            cur.execute("INSERT OR IGNORE INTO teacher_subjects (teacher_id, subject_id) VALUES (?, ?)", 
                       (teacher_id, subject_id))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Teacher added successfully'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Username already exists'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/edit_teacher/<int:teacher_id>', methods=['POST'])
def edit_teacher(teacher_id):
    username = request.form['username']
    password = request.form.get('password', '')
    subject_ids = request.form.getlist('subjects')
    
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    
    try:
        # Update teacher
        if password:
            cur.execute("UPDATE teachers SET username = ?, password = ? WHERE id = ?", 
                       (username, password, teacher_id))
        else:
            cur.execute("UPDATE teachers SET username = ? WHERE id = ?", (username, teacher_id))
        
        # Update teacher subjects
        cur.execute("DELETE FROM teacher_subjects WHERE teacher_id = ?", (teacher_id,))
        for subject_id in subject_ids:
            cur.execute("INSERT INTO teacher_subjects (teacher_id, subject_id) VALUES (?, ?)", 
                       (teacher_id, subject_id))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Teacher updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/delete_teacher/<int:teacher_id>', methods=['POST'])
def delete_teacher(teacher_id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    
    try:
        # Delete teacher subjects first
        cur.execute("DELETE FROM teacher_subjects WHERE teacher_id = ?", (teacher_id,))
        # Delete teacher
        cur.execute("DELETE FROM teachers WHERE id = ?", (teacher_id,))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Teacher deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

# ===== SUBJECT MANAGEMENT ROUTES =====
@app.route('/manage_subjects')
def manage_subjects():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Get all subjects with teacher count
    cur.execute('''
        SELECT s.id, s.subject_name, s.subject_code, s.description,
               COUNT(ts.teacher_id) as teacher_count
        FROM subjects s
        LEFT JOIN teacher_subjects ts ON s.id = ts.subject_id
        GROUP BY s.id, s.subject_name, s.subject_code, s.description
        ORDER BY s.subject_name
    ''')
    subjects = cur.fetchall()
    
    conn.close()
    return render_template('manage_subjects.html', subjects=subjects)

@app.route('/add_subject', methods=['POST'])
def add_subject():
    subject_name = request.form['subject_name']
    subject_code = request.form['subject_code']
    description = request.form.get('description', '')
    
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    
    try:
        cur.execute("INSERT INTO subjects (subject_name, subject_code, description) VALUES (?, ?, ?)", 
                   (subject_name, subject_code, description))
        conn.commit()
        return jsonify({'success': True, 'message': 'Subject added successfully'})
   
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Subject name or code already exists'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/edit_subject/<int:subject_id>', methods=['POST'])
def edit_subject(subject_id):
    subject_name = request.form['subject_name']
    subject_code = request.form['subject_code']
    description = request.form.get('description', '')
    
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    
    try:
        cur.execute("UPDATE subjects SET subject_name = ?, subject_code = ?, description = ? WHERE id = ?", 
                   (subject_name, subject_code, description, subject_id))
        conn.commit()
        return jsonify({'success': True, 'message': 'Subject updated successfully'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Subject name or code already exists'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/delete_subject/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    
    try:
        # Delete teacher-subject mappings first
        cur.execute("DELETE FROM teacher_subjects WHERE subject_id = ?", (subject_id,))
        # Delete subject
        cur.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Subject deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

# === PWA Service Worker Route ===
@app.route('/static/sw.js')
def service_worker():
    """Serve service worker with correct MIME type"""
    return send_file('static/sw.js', mimetype='application/javascript')

if __name__ == '__main__':
    # Fast startup with IP filtering
    import logging
    
    # Optimize logging for speed
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    # Fast IP filter
    class QuickIPFilter(logging.Filter):
        def filter(self, record):
            msg = str(record.msg)
            return not ('192.168.' in msg or '10.0.' in msg or '172.' in msg or 'PIN:' in msg)
    
    # Apply filter
    logging.getLogger('werkzeug').addFilter(QuickIPFilter())
    
    # Print custom startup message in your preferred order
    print("WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.")
    print(" * Running on all addresses (0.0.0.0)")
    print(" * Running on http://127.0.0.1:5000")
    print(" * Serving Flask app 'main'")
    print(" * Debug mode: on")
    
    # Fast startup configuration
    app.run(
        debug=True, 
        host='0.0.0.0', 
        port=5000,
        threaded=True,
        use_reloader=False,  # Disable reloader for faster startup
        use_debugger=False   # Disable debugger for speed
    )

from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = '123'

@app.route('/')
def home():
    return render_template('index.html')

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
            return redirect(url_for('student_home'))
        else:
            flash("Invalid credentials", "danger")
    
    return render_template('student_login.html')

@app.route('/student_home')
def student_home():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    
    student_id = session.get('student_id')
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM users WHERE student_id = ?", (student_id,))
    student = cur.fetchone()
    
    if not student:
        flash("Student not found", "error")
        return redirect(url_for('student_login'))
    
    conn.close()
    return render_template('student_home.html', student=student)

if __name__ == '__main__':
    print("Starting simplified Flask app...")
    app.run(debug=True, host='0.0.0.0', port=5002)

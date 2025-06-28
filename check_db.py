import sqlite3

conn = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute('SELECT name, student_id, image_path FROM users')
users = cur.fetchall()

print('Registered Users:')
for user in users:
    print(f'Name: {user["name"]}, ID: {user["student_id"]}, Image: {user["image_path"]}')

conn.close()

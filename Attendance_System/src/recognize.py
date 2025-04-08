import cv2
import face_recognition
import pickle
import sqlite3
from datetime import datetime

# Load trained encodings
encoding_file = "../models/encodings.pickle"
data = pickle.loads(open(encoding_file, "rb").read())

# Connect to database
conn = sqlite3.connect('../database/attendance.db')
cursor = conn.cursor()

# Start webcam
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    for encoding, location in zip(face_encodings, face_locations):
        matches = face_recognition.compare_faces(data["encodings"], encoding)
        name = "Unknown"

        if True in matches:
            matched_indexes = [i for i, match in enumerate(matches) if match]
            name = data["names"][matched_indexes[0]]

            # Mark attendance
            date_today = datetime.now().strftime('%Y-%m-%d')
            time_now = datetime.now().strftime('%H:%M:%S')

            cursor.execute("INSERT INTO attendance (name, date, time) VALUES (?, ?, ?)",
                           (name, date_today, time_now))
            conn.commit()

            print(f"✅ Attendance marked for {name} at {time_now} on {date_today}")

        # Display result
        top, right, bottom, left = location
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, name, (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    cv2.imshow("Face Recognition", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
conn.close()

import cv2
import os
import csv
import matplotlib.pyplot as plt

# Paths
dataset_path = "../dataset/"
metadata_file = "../dataset/metadata.csv"

# Ensure dataset directory exists
if not os.path.exists(dataset_path):
    os.makedirs(dataset_path)

# Get user details
person_id = input("Enter Person ID: ")
name = input("Enter Person's Name: ")
department = input("Enter Department: ")

# Create a folder for the person
person_path = os.path.join(dataset_path, f"{person_id}_{name}")
if not os.path.exists(person_path):
    os.makedirs(person_path)

# Save metadata (if not already saved)
metadata_exists = os.path.exists(metadata_file)
with open(metadata_file, "a", newline="") as file:
    writer = csv.writer(file)
    if not metadata_exists:
        writer.writerow(["ID", "Name", "Department"])  # Write header
    writer.writerow([person_id, name, department])

# Initialize webcam
cap = cv2.VideoCapture(0)
face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

print(f"Capturing images for {name}... Press 'q' to stop.")

count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_detector.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        count += 1
        face = frame[y:y+h, x:x+w]
        cv2.imwrite(f"{person_path}/{count}.jpg", face)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    plt.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    plt.title("Face Capture")
    plt.axis("off")
    plt.show()

    if count >= 2 or cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

print(f"✅ {count} images saved for {name}.")
print(f"✅ Person's details saved in metadata.csv")

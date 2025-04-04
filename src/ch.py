import face_recognition
import cv2
import os

dataset_path = "C:\\Users\\attar\\OneDrive\\Desktop\\project\\Attendance_System\\dataset"

for name in os.listdir(dataset_path):
    person_path = os.path.join(dataset_path, name)

    if not os.path.isdir(person_path):
        continue  

    for image_name in os.listdir(person_path):
        image_path = os.path.join(person_path, image_name)
        image = cv2.imread(image_path)

        if image is None:
            print(f"❌ Failed to load {image_path}")
            continue

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb_image)

        if len(encodings) > 0:
            print(f"✅ Face detected in {image_path}")
        else:
            print(f"⚠ No face found in {image_path} ❌")

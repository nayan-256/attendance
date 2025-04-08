import face_recognition
import pickle
import os
import cv2

# Path to dataset containing images of known faces
dataset_path = "C:\\Users\\attar\\OneDrive\\Desktop\\project\\Attendance_System\\dataset"
encoding_file = "C:\\Users\\attar\\OneDrive\\Desktop\\project\\Attendance_System\\models\\encoding.pickle"

known_encodings = []
known_names = []

# Loop through all images in the dataset folder
for name in os.listdir(dataset_path):
    person_path = os.path.join(dataset_path, name)
    
    if not os.path.isdir(person_path):
        continue  # Skip if it's not a folder

    for image_name in os.listdir(person_path):
        image_path = os.path.join(person_path, image_name)
        image = cv2.imread(image_path)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        encodings = face_recognition.face_encodings(rgb_image)
        if len(encodings) > 0:
            known_encodings.append(encodings[0])
            known_names.append(name)

# Save the encodings to a file
data = {"encodings": known_encodings, "names": known_names}
with open(encoding_file, "wb") as file:
    file.write(pickle.dumps(data))

print(f"✅ Encodings saved successfully! {len(known_names)} faces encoded.")

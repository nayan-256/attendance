import face_recognition
import pickle
import os
import csv
import cv2

# Paths
dataset_path = "../dataset/"
metadata_file = "../dataset/metadata.csv"
encoding_file = "../models/encodings.pickle"

known_encodings = []
known_names = {}

# Load metadata
if os.path.exists(metadata_file):
    with open(metadata_file, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            known_names[row["ID"]] = f"{row['Name']} ({row['Department']})"


print("Training model...")

# Loop through each person's folder
# Loop through each person's folder
for person_folder in os.listdir(dataset_path):
    folder_path = os.path.join(dataset_path, person_folder)

    # Skip if it's not a directory
    if not os.path.isdir(folder_path):
        continue

    person_id = person_folder.split("_")[0]  # Extract ID
    person_name = known_names.get(person_id, "Unknown")

    for img_name in os.listdir(folder_path):
        img_path = os.path.join(folder_path, img_name)

        # Ensure it's an image file (optional check)
        if not img_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue

        image = cv2.imread(img_path)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        face_encodings = face_recognition.face_encodings(rgb_image)
        if len(face_encodings) > 0:
            known_encodings.append(face_encodings[0])
            known_names[person_id] = person_name  # Save name from metadata

# Save encodings
data = {"encodings": known_encodings, "names": list(known_names.values())}
with open(encoding_file, "wb") as f:
    pickle.dump(data, f)

print("✅ Model training complete. Encodings saved!")

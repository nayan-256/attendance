import os

# Check if encoding file exists and is not empty
if not os.path.exists(encoding.pickle) or os.path.getsize(encoding.pickle) == 0:
    print("⚠️ Encoding file is missing or empty!")
    exit()

# Load trained encodings
with open(encoding_file, "rb") as f:
    data = pickle.load(f)

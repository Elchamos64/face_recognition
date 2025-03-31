import os
import json
from imutils import paths
import face_recognition
import pickle
import cv2

def load_metadata(imagePath):
    metadata_file = os.path.join("dataset", imagePath.split(os.path.sep)[-2], "metadata.json")
    if os.path.exists(metadata_file):
        with open(metadata_file, "r") as f:
            metadata_list = json.load(f)
            for entry in metadata_list:
                if entry["filename"] in imagePath:
                    return entry["occupation"], entry["age"]
    return None, None  # Default if no metadata found

print("[INFO] Start processing faces...")
imagePaths = list(paths.list_images("dataset"))
knownEncodings = []
knownNames = []
knownOccupations = []
knownAges = []

for (i, imagePath) in enumerate(imagePaths):
    print(f"[INFO] Processing image {i + 1}/{len(imagePaths)}")
    name = imagePath.split(os.path.sep)[-2]
    occupation, age = load_metadata(imagePath)
    
    image = cv2.imread(imagePath)
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    boxes = face_recognition.face_locations(rgb, model="hog")
    encodings = face_recognition.face_encodings(rgb, boxes)
    
    for encoding in encodings:
        knownEncodings.append(encoding)
        knownNames.append(name)
        knownOccupations.append(occupation)
        knownAges.append(age)

print("[INFO] Serializing encodings...")
data = {
    "encodings": knownEncodings,
    "names": knownNames,
    "occupations": knownOccupations,
    "ages": knownAges
}

with open("encodings.pickle", "wb") as f:
    f.write(pickle.dumps(data))

print("[INFO] Training complete. Encodings saved to 'encodings.pickle'")


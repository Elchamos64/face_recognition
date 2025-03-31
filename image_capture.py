import cv2
import os
import json
from datetime import datetime
from picamera2 import Picamera2
import time

# Change these to the person's details
PERSON_NAME = "oscar"
OCCUPATION = "Engineer"
AGE = 24

def create_folder(name):
    dataset_folder = "dataset"
    if not os.path.exists(dataset_folder):
        os.makedirs(dataset_folder)
    
    person_folder = os.path.join(dataset_folder, name)
    if not os.path.exists(person_folder):
        os.makedirs(person_folder)
    return person_folder

def save_metadata(name, filename, occupation, age):
    metadata = {
        "name": name,
        "filename": filename,
        "occupation": occupation,
        "age": age,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    metadata_file = os.path.join("dataset", name, "metadata.json")
    
    if os.path.exists(metadata_file):
        with open(metadata_file, "r") as f:
            data = json.load(f)
    else:
        data = []
    
    data.append(metadata)
    
    with open(metadata_file, "w") as f:
        json.dump(data, f, indent=4)
    
    print(f"Metadata saved for {filename}")

def capture_photos(name, occupation, age):
    folder = create_folder(name)
    
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
    picam2.start()
    
    time.sleep(2)
    
    photo_count = 0
    
    print(f"Taking photos for {name}. Press SPACE to capture, 'q' to quit.")
    
    while True:
        frame = picam2.capture_array()
        cv2.imshow('Capture', frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord(' '):  # Space key
            photo_count += 1
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.jpg"
            filepath = os.path.join(folder, filename)
            cv2.imwrite(filepath, frame)
            
            save_metadata(name, filename, occupation, age)
            print(f"Photo {photo_count} saved: {filepath}")
        
        elif key == ord('q'):  # Q key
            break
    
    cv2.destroyAllWindows()
    picam2.stop()
    print(f"Photo capture completed. {photo_count} photos saved for {name}.")

if __name__ == "__main__":
    capture_photos(PERSON_NAME, OCCUPATION, AGE)

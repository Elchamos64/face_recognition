import tkinter as tk
from tkinter import Label
from PIL import Image, ImageTk
import face_recognition
import cv2
import numpy as np
from picamera2 import Picamera2
import time
import pickle
import pyttsx3
import threading

# === Load face encodings with metadata ===
with open("encodings.pickle", "rb") as f:
    data = pickle.loads(f.read())
known_face_encodings = data["encodings"]
known_face_names = data["names"]
known_face_ages = data.get("ages", [])
known_face_occupations = data.get("occupations", [])

# === Text-to-speech engine ===
engine = pyttsx3.init(driverName='espeak')
engine.setProperty('rate', 150)

# === Setup Camera ===
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()

# === Global state ===
cv_scaler = 4
face_locations = []
face_encodings = []
face_names = []
face_ages = []
face_occupations = []
last_spoken_name = None
frame_count = 0
start_time = time.time()
fps = 0

# === Speech Queue Setup ===
speech_queue = []
speech_lock = threading.Lock()

def speech_worker():
    while True:
        if speech_queue:
            with speech_lock:
                message = speech_queue.pop(0)
            engine.say(message)
            engine.runAndWait()
        else:
            time.sleep(0.1)

speech_thread = threading.Thread(target=speech_worker, daemon=True)
speech_thread.start()

# === Speak name and metadata if new, using queue ===
def speak_name(name, age, occupation):
    global last_spoken_name, speech_queue
    if name != "Unknown" and name != last_spoken_name:
         message = f"Name: {name}, Age: {age}, Occupation: {occupation}"
         with speech_lock:
             speech_queue.append(message)
         last_spoken_name = name

# === Process frame and run recognition ===
def process_frame(frame):
    global face_locations, face_encodings, face_names, face_ages, face_occupations
    resized_frame = cv2.resize(frame, (0, 0), fx=1/cv_scaler, fy=1/cv_scaler)
    rgb_resized = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_resized)
    face_encodings = face_recognition.face_encodings(rgb_resized, face_locations, model='large')
    face_names = []
    face_ages = []
    face_occupations = []

    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Unknown"
        age = "Unknown"
        occupation = "Unknown"

        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        if len(face_distances) > 0:
            best_index = np.argmin(face_distances)
            if matches[best_index]:
                name = known_face_names[best_index]
                age = known_face_ages[best_index] if known_face_ages else "Unknown"
                occupation = known_face_occupations[best_index] if known_face_occupations else "Unknown"

        face_names.append(name)
        face_ages.append(age)
        face_occupations.append(occupation)
        speak_name(name, age, occupation)

    return frame

# === Draw bounding boxes and only name on video feed ===
def draw_results(frame):
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        top *= cv_scaler
        right *= cv_scaler
        bottom *= cv_scaler
        left *= cv_scaler

        cv2.rectangle(frame, (left, top), (right, bottom), (244, 42, 3), 3)
        # Draw a filled rectangle above the face for the name label
        cv2.rectangle(frame, (left-3, top-30), (right+3, top), (244, 42, 3), cv2.FILLED)
        cv2.putText(frame, name, (left+6, top-8), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255,255,255), 1)
    return frame

# === FPS calculation ===
def calculate_fps():
    global frame_count, start_time, fps
    frame_count += 1
    elapsed = time.time() - start_time
    if elapsed > 1:
        fps = frame_count / elapsed
        frame_count = 0
        start_time = time.time()
    return fps

# === Tkinter UI Setup ===
window = tk.Tk()
window.title("Face Recognition UI")
window.geometry("1300x600")
window.configure(bg='black')

# Create a details frame on the left for displaying person info
details_frame = tk.Frame(window, bg="black")
details_frame.pack(side="left", padx=10, pady=10, fill="both", expand=False)

# Create a video frame on the right for the live feed
video_frame = tk.Frame(window, bg="black")
video_frame.pack(side="right", padx=10, pady=10, fill="both", expand=True)

video_label = Label(video_frame)
video_label.pack(padx=10, pady=10)

output_label = Label(details_frame, text="", font=("Helvetica", 16), bg="black", fg="white", justify="left")
output_label.pack(padx=10, pady=10, fill="both", expand=True)

# === Main loop to update frames ===
def update_frame():
    try:
        frame = picam2.capture_array()
        process_frame(frame)
        draw_results(frame)
        current_fps = calculate_fps()

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        img = img.resize((640, 480))
        imgtk = ImageTk.PhotoImage(image=img)
        video_label.imgtk = imgtk
        video_label.configure(image=imgtk)

        # Format detected persons' details in a nice way
        if face_names:
            detected_text = ""
            for n, a, o in zip(face_names, face_ages, face_occupations):
                detected_text += f"Name: {n}\nAge: {a}\nOccupation: {o}\n\n"
        else:
            detected_text = "No faces detected"
        output_label.config(text=f"{detected_text}\nFPS: {current_fps:.2f}")
    except Exception as e:
        print(f"[ERROR] {e}")

    window.after(10, update_frame)

# === Clean shutdown ===
def on_close():
    picam2.stop()
    window.destroy()

window.protocol("WM_DELETE_WINDOW", on_close)
update_frame()
window.mainloop()

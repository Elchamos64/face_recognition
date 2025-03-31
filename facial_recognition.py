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

# === Load face encodings ===
with open("encodings.pickle", "rb") as f:
    data = pickle.loads(f.read())
known_face_encodings = data["encodings"]
known_face_names = data["names"]

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
last_spoken_name = None
frame_count = 0
start_time = time.time()
fps = 0

# === Speak name if new ===
def speak_name(name):
    global last_spoken_name
    if name != last_spoken_name and name != "Unknown":
        engine.say(f"Hello, my name is {name}")
        engine.runAndWait()
        last_spoken_name = name

# === Process frame and run recognition ===
def process_frame(frame):
    global face_locations, face_encodings, face_names
    resized_frame = cv2.resize(frame, (0, 0), fx=1/cv_scaler, fy=1/cv_scaler)
    rgb_resized = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_resized)
    face_encodings = face_recognition.face_encodings(rgb_resized, face_locations, model='large')
    face_names = []

    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Unknown"

        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        if len(face_distances) > 0:
            best_index = np.argmin(face_distances)
            if matches[best_index]:
                name = known_face_names[best_index]

        face_names.append(name)
        speak_name(name)

    return frame

# === Draw bounding boxes and names ===
def draw_results(frame):
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        top *= cv_scaler
        right *= cv_scaler
        bottom *= cv_scaler
        left *= cv_scaler

        cv2.rectangle(frame, (left, top), (right, bottom), (244, 42, 3), 3)
        cv2.rectangle(frame, (left-3, top-35), (right+3, top), (244, 42, 3), cv2.FILLED)
        cv2.putText(frame, name, (left+6, top-6), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255,255,255), 1)
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

# === Tkinter UI ===
window = tk.Tk()
window.title("Face Recognition UI")
window.geometry("1300x600")
window.configure(bg='black')

video_label = Label(window)
video_label.pack(side="left", padx=10, pady=10)

output_label = Label(window, text="", font=("Helvetica", 16), bg="black", fg="white", justify="left")
output_label.pack(side="right", padx=10, pady=10, fill="both", expand=True)

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

        detected = "\n".join(face_names) if face_names else "No faces detected"
        output_label.config(text=f"Detected:\n{detected}\n\nFPS: {current_fps:.2f}")
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

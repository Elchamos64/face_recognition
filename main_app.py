import tkinter as tk
from tkinter import ttk, messagebox, Label
from PIL import Image, ImageTk
import cv2
import os
import json
import time
import threading
from datetime import datetime
from picamera2 import Picamera2
import face_recognition
import pickle
import numpy as np
import pyttsx3
from imutils import paths
import mysql.connector

##############################
# Database Manager
##############################
class DatabaseManager:
    def __init__(self, host='localhost', user='root', password='Right1234', database='face_recognition_db'):
        try:
            self.cnx = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Right1234',
    unix_socket='/var/run/mysqld/mysqld.sock'
)

            self.cnx.autocommit = True
            self.cursor = self.cnx.cursor()
        except Exception as e:
            raise Exception(f"Failed to connect to MySQL: {e}")
        self.database = database
        self.create_database()
        self.cnx.database = database
        self.create_tables()
    
    def create_database(self):
        self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
    
    def create_tables(self):
        # Create persons table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS persons (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            occupation VARCHAR(255),
            age INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        # Create images table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INT AUTO_INCREMENT PRIMARY KEY,
            person_id INT,
            filename VARCHAR(255),
            image LONGBLOB,
            timestamp DATETIME,
            FOREIGN KEY (person_id) REFERENCES persons(id)
        )
        """)
        # Create encodings table (store one row with the pickled encodings)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS encodings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            data LONGBLOB,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """)
    
    def add_person(self, name, occupation, age):
        query = "SELECT id FROM persons WHERE name = %s"
        self.cursor.execute(query, (name,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        else:
            query = "INSERT INTO persons (name, occupation, age) VALUES (%s, %s, %s)"
            self.cursor.execute(query, (name, occupation, age))
            return self.cursor.lastrowid
    
    def add_image(self, person_id, filename, image_data, timestamp):
        query = "INSERT INTO images (person_id, filename, image, timestamp) VALUES (%s, %s, %s, %s)"
        self.cursor.execute(query, (person_id, filename, image_data, timestamp))
    
    def get_all_images(self):
        query = """
        SELECT p.name, p.occupation, p.age, i.image
        FROM images i
        JOIN persons p ON i.person_id = p.id
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def update_encodings(self, data):
        # If there is already a row, update it; otherwise insert a new row
        query = "SELECT id FROM encodings LIMIT 1"
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        if result:
            query = "UPDATE encodings SET data = %s WHERE id = %s"
            self.cursor.execute(query, (data, result[0]))
        else:
            query = "INSERT INTO encodings (data) VALUES (%s)"
            self.cursor.execute(query, (data,))
    
    def get_encodings(self):
        query = "SELECT data FROM encodings ORDER BY updated_at DESC LIMIT 1"
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return None

    def close(self):
        self.cursor.close()
        self.cnx.close()

##############################
# Capture Page
##############################
class CaptureFrame(tk.Frame):
    def __init__(self, parent, camera, db_manager):
        super().__init__(parent, bg="black")
        self.parent = parent
        self.camera = camera
        self.db_manager = db_manager
        self.running = False

        # Layout: video feed on left, form on right
        self.video_label = tk.Label(self, bg="black")
        self.video_label.pack(side="left", padx=10, pady=10)

        form_frame = tk.Frame(self, bg="black")
        form_frame.pack(side="right", padx=10, pady=10, fill="both", expand=True)

        ttk.Label(form_frame, text="Name:", font=("Arial", 14)).pack(anchor="w", pady=(10,0))
        self.name_entry = ttk.Entry(form_frame, font=("Arial", 14))
        self.name_entry.pack(fill="x", padx=5, pady=5)

        ttk.Label(form_frame, text="Occupation:", font=("Arial", 14)).pack(anchor="w", pady=(10,0))
        self.occupation_entry = ttk.Entry(form_frame, font=("Arial", 14))
        self.occupation_entry.pack(fill="x", padx=5, pady=5)

        ttk.Label(form_frame, text="Age:", font=("Arial", 14)).pack(anchor="w", pady=(10,0))
        self.age_var = tk.StringVar()
        self.age_dropdown = ttk.Combobox(form_frame, textvariable=self.age_var, font=("Arial", 14), state="readonly")
        self.age_dropdown['values'] = [str(i) for i in range(1, 101)]
        self.age_dropdown.set("25")
        self.age_dropdown.pack(fill="x", padx=5, pady=5)

        self.capture_btn = ttk.Button(form_frame, text="Capture Photo", command=self.capture_photo)
        self.capture_btn.pack(pady=20)

    def capture_photo(self):
        name = self.name_entry.get().strip()
        occupation = self.occupation_entry.get().strip()
        age = self.age_var.get().strip()
        if not name or not occupation or not age:
            messagebox.showerror("Missing Info", "Please fill in all fields.")
            return

        frame = self.camera.capture_array()
        # Encode the frame to JPEG bytes
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            messagebox.showerror("Error", "Failed to encode image.")
            return
        image_bytes = buffer.tobytes()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = f"{name}_{timestamp}.jpg"
        # Add or get person ID
        person_id = self.db_manager.add_person(name, occupation, int(age))
        # Save image into the DB
        self.db_manager.add_image(person_id, filename, image_bytes, timestamp)
        messagebox.showinfo("Saved", f"Photo saved for {name}")

    def update_frame(self):
        if not self.running:
            return
        try:
            frame = self.camera.capture_array()
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            img = img.resize((640, 480))
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
        except Exception as e:
            print(f"[CaptureFrame ERROR] {e}")
        self.after(10, self.update_frame)

    def start_camera(self):
        if not self.running:
            self.running = True
            self.update_frame()

    def stop_camera(self):
        self.running = False

##############################
# Training Page
##############################
class TrainFrame(tk.Frame):
    def __init__(self, parent, db_manager):
        super().__init__(parent, bg="black")
        self.parent = parent
        self.db_manager = db_manager

        self.info_label = ttk.Label(self, text="Press the button below to train the model.", font=("Arial", 14))
        self.info_label.pack(pady=20)
        self.train_btn = ttk.Button(self, text="Train Model", command=self.start_training)
        self.train_btn.pack(pady=10)
        self.status_label = ttk.Label(self, text="", font=("Arial", 12))
        self.status_label.pack(pady=10)

    def start_training(self):
        self.status_label.config(text="Training in progress...")
        threading.Thread(target=self.train_model, daemon=True).start()

    def train_model(self):
        rows = self.db_manager.get_all_images()
        knownEncodings = []
        knownNames = []
        knownOccupations = []
        knownAges = []
        total = len(rows)
        print(f"[TRAIN] Found {total} images in the database.")
        for (i, row) in enumerate(rows):
            print(f"[TRAIN] Processing image {i + 1}/{total}")
            name, occupation, age, image_data = row
            # Convert binary image to cv2 image
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(rgb, model="hog")
            encodings = face_recognition.face_encodings(rgb, boxes)
            for encoding in encodings:
                knownEncodings.append(encoding)
                knownNames.append(name)
                knownOccupations.append(occupation)
                knownAges.append(age)
        # Serialize the encodings data
        data = {
            "encodings": knownEncodings,
            "names": knownNames,
            "occupations": knownOccupations,
            "ages": knownAges
        }
        pickled_data = pickle.dumps(data)
        self.db_manager.update_encodings(pickled_data)
        print("[TRAIN] Training complete. Encodings updated in the database.")
        self.status_label.config(text="Training complete.")

##############################
# Recognition Page
##############################
class RecognizeFrame(tk.Frame):
    def __init__(self, parent, camera, db_manager):
        super().__init__(parent, bg="black")
        self.parent = parent
        self.camera = camera
        self.db_manager = db_manager
        self.running = False

        # Setup TTS engine and speech queue
        self.engine = pyttsx3.init(driverName='espeak')
        self.engine.setProperty('rate', 150)
        self.speech_queue = []
        self.speech_lock = threading.Lock()
        self.last_spoken_name = None
        threading.Thread(target=self.speech_worker, daemon=True).start()

        # Load encodings from DB
        enc_data = self.db_manager.get_encodings()
        if enc_data:
            try:
                data = pickle.loads(enc_data)
                self.known_face_encodings = data["encodings"]
                self.known_face_names = data["names"]
                self.known_face_occupations = data.get("occupations", [])
                self.known_face_ages = data.get("ages", [])
            except Exception as e:
                messagebox.showerror("Error", f"Error loading encodings: {e}")
                self.known_face_encodings = []
                self.known_face_names = []
                self.known_face_occupations = []
                self.known_face_ages = []
        else:
            messagebox.showerror("Error", "No encodings found in database. Please train the model first.")
            self.known_face_encodings = []
            self.known_face_names = []
            self.known_face_occupations = []
            self.known_face_ages = []

        self.cv_scaler = 4
        self.face_locations = []
        self.face_encodings = []
        self.face_names = []
        self.face_ages = []
        self.face_occupations = []
        self.frame_count = 0
        self.start_time = time.time()
        self.fps = 0

        # Layout: details on left, video feed on right
        self.details_frame = tk.Frame(self, bg="black")
        self.details_frame.pack(side="left", padx=10, pady=10, fill="both", expand=False)
        self.details_label = tk.Label(self.details_frame, text="", font=("Helvetica", 16), bg="black", fg="white", justify="left")
        self.details_label.pack(padx=10, pady=10, fill="both", expand=True)

        self.video_frame = tk.Frame(self, bg="black")
        self.video_frame.pack(side="right", padx=10, pady=10, fill="both", expand=True)
        self.video_label = tk.Label(self.video_frame, bg="black")
        self.video_label.pack(padx=10, pady=10)

    def speech_worker(self):
        while True:
            if self.speech_queue:
                with self.speech_lock:
                    message = self.speech_queue.pop(0)
                self.engine.say(message)
                self.engine.runAndWait()
            else:
                time.sleep(0.1)

    def speak_name(self, name, age, occupation):
        if name != "Unknown" and name != self.last_spoken_name:
            message = f"Name: {name}, Age: {age}, Occupation: {occupation}"
            with self.speech_lock:
                self.speech_queue.append(message)
            self.last_spoken_name = name

    def process_frame(self, frame):
        resized_frame = cv2.resize(frame, (0, 0), fx=1/self.cv_scaler, fy=1/self.cv_scaler)
        rgb_resized = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
        self.face_locations = face_recognition.face_locations(rgb_resized)
        self.face_encodings = face_recognition.face_encodings(rgb_resized, self.face_locations, model='large')
        self.face_names = []
        self.face_ages = []
        self.face_occupations = []
        for face_encoding in self.face_encodings:
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
            name = "Unknown"
            age = "Unknown"
            occupation = "Unknown"
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            if len(face_distances) > 0:
                best_index = np.argmin(face_distances)
                if matches[best_index]:
                    name = self.known_face_names[best_index]
                    age = self.known_face_ages[best_index] if self.known_face_ages else "Unknown"
                    occupation = self.known_face_occupations[best_index] if self.known_face_occupations else "Unknown"
            self.face_names.append(name)
            self.face_ages.append(age)
            self.face_occupations.append(occupation)
            self.speak_name(name, age, occupation)
        return frame

    def draw_results(self, frame):
        for (top, right, bottom, left), name in zip(self.face_locations, self.face_names):
            top *= self.cv_scaler
            right *= self.cv_scaler
            bottom *= self.cv_scaler
            left *= self.cv_scaler
            cv2.rectangle(frame, (left, top), (right, bottom), (244, 42, 3), 3)
            cv2.rectangle(frame, (left-3, top-30), (right+3, top), (244, 42, 3), cv2.FILLED)
            cv2.putText(frame, name, (left+6, top-8), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255,255,255), 1)
        return frame

    def calculate_fps(self):
        self.frame_count += 1
        elapsed = time.time() - self.start_time
        if elapsed > 1:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.start_time = time.time()
        return self.fps

    def update_frame(self):
        if not self.running:
            return
        try:
            frame = self.camera.capture_array()
            self.process_frame(frame)
            self.draw_results(frame)
            current_fps = self.calculate_fps()

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            img = img.resize((640, 480))
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

            if self.face_names:
                details = ""
                for n, a, o in zip(self.face_names, self.face_ages, self.face_occupations):
                    details += f"Name: {n}\nAge: {a}\nOccupation: {o}\n\n"
            else:
                details = "No faces detected"
            self.details_label.config(text=f"{details}\nFPS: {current_fps:.2f}")
        except Exception as e:
            print(f"[RecognizeFrame ERROR] {e}")
        self.after(10, self.update_frame)

    def start_camera(self):
        if not self.running:
            self.running = True
            self.update_frame()

    def stop_camera(self):
        self.running = False

##############################
# Main App with Navigation and Custom Theme
##############################
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Face Recognition Suite")
        self.geometry("1300x700")
        self.configure(bg="black")

        # Create and initialize database
        try:
            self.db_manager = DatabaseManager(host='localhost', user='root', password='', database='face_recognition_db')
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            self.destroy()
            return

        # Use ttk style and set a custom theme (orange, grey, black)
        style = ttk.Style(self)
        style.theme_use("clam")
        # Customize some style options (buttons, labels)
        style.configure("TButton", background="#555555", foreground="white", font=("Arial", 14))
        style.map("TButton", background=[("active", "#FFA500")])
        style.configure("TLabel", background="black", foreground="white", font=("Arial", 14))

        # Create a single shared camera instance
        try:
            self.camera = Picamera2()
            self.camera.configure(self.camera.create_preview_configuration(
                main={"format": 'XRGB8888', "size": (640, 480)}
            ))
            self.camera.start()
        except Exception as e:
            messagebox.showerror("Camera Error", f"Failed to initialize camera: {e}")
            self.camera = None

        # Navigation sidebar with custom colors (grey background, orange accents)
        nav_frame = tk.Frame(self, bg="#333333")
        nav_frame.pack(side="left", fill="y")
        btn_style = {"font": ("Arial", 14), "bg": "#555555", "fg": "white", 
                     "activebackground": "#FFA500", "bd": 0, "relief": tk.FLAT, "highlightthickness": 0}

        self.btn_capture = tk.Button(nav_frame, text="Capture", command=lambda: self.show_frame("capture"), **btn_style)
        self.btn_capture.pack(fill="x", pady=5, padx=10)
        self.btn_train = tk.Button(nav_frame, text="Train", command=lambda: self.show_frame("train"), **btn_style)
        self.btn_train.pack(fill="x", pady=5, padx=10)
        self.btn_recognize = tk.Button(nav_frame, text="Recognize", command=lambda: self.show_frame("recognize"), **btn_style)
        self.btn_recognize.pack(fill="x", pady=5, padx=10)

        # Container for pages
        container = tk.Frame(self, bg="black")
        container.pack(side="right", fill="both", expand=True)

        self.frames = {}
        # Pass the shared camera and db_manager to pages that need them
        self.frames["capture"] = CaptureFrame(container, self.camera, self.db_manager) if self.camera else CaptureFrame(container, None, self.db_manager)
        self.frames["train"] = TrainFrame(container, self.db_manager)
        self.frames["recognize"] = RecognizeFrame(container, self.camera, self.db_manager) if self.camera else RecognizeFrame(container, None, self.db_manager)
        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

        self.current_frame = None
        self.show_frame("capture")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def show_frame(self, name):
        # Pause any camera pages before switching
        for key in ["capture", "recognize"]:
            if key in self.frames:
                self.frames[key].stop_camera()
        frame = self.frames[name]
        frame.tkraise()
        self.current_frame = name
        # Start camera if needed
        if name in ["capture", "recognize"]:
            frame.start_camera()

    def on_close(self):
        if self.camera:
            self.camera.stop()
        self.db_manager.close()
        self.destroy()

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()

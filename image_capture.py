import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import cv2
import os
import json
from datetime import datetime
from picamera2 import Picamera2
import time

# === Setup folders ===
def create_folder(name):
    dataset_folder = "dataset"
    if not os.path.exists(dataset_folder):
        os.makedirs(dataset_folder)
    
    person_folder = os.path.join(dataset_folder, name)
    if not os.path.exists(person_folder):
        os.makedirs(person_folder)
    return person_folder

# === Save metadata to JSON ===
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

# === Camera Setup ===
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()
time.sleep(2)

# === Tkinter Setup ===
window = tk.Tk()
window.title("Face Dataset Collector")
window.geometry("1300x600")
window.configure(bg="black")

# Left: Video feed
video_label = tk.Label(window)
video_label.pack(side="left", padx=10, pady=10)

# Right: Form
form_frame = tk.Frame(window, bg="black")
form_frame.pack(side="right", padx=10, pady=10, fill="both", expand=True)

# Form fields
tk.Label(form_frame, text="Name:", fg="white", bg="black", font=("Arial", 14)).pack(anchor="w")
name_entry = tk.Entry(form_frame, font=("Arial", 14))
name_entry.pack(fill="x")

tk.Label(form_frame, text="Occupation:", fg="white", bg="black", font=("Arial", 14)).pack(anchor="w", pady=(10,0))
occupation_entry = tk.Entry(form_frame, font=("Arial", 14))
occupation_entry.pack(fill="x")

tk.Label(form_frame, text="Age:", fg="white", bg="black", font=("Arial", 14)).pack(anchor="w", pady=(10,0))
age_var = tk.StringVar()
age_dropdown = ttk.Combobox(form_frame, textvariable=age_var, font=("Arial", 14), state="readonly")
age_dropdown['values'] = [str(i) for i in range(1, 101)]
age_dropdown.set("25")
age_dropdown.pack(fill="x")

# Capture photo
def capture_photo():
    name = name_entry.get().strip()
    occupation = occupation_entry.get().strip()
    age = age_var.get().strip()

    if not name or not occupation or not age:
        messagebox.showerror("Missing Info", "Please fill in all fields.")
        return

    folder = create_folder(name)
    frame = picam2.capture_array()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.jpg"
    filepath = os.path.join(folder, filename)
    cv2.imwrite(filepath, frame)
    
    save_metadata(name, filename, occupation, age)
    messagebox.showinfo("Saved", f"Photo saved for {name}")

capture_btn = tk.Button(form_frame, text="Capture Photo", font=("Arial", 16), command=capture_photo)
capture_btn.pack(pady=20)

# Update live camera feed
def update_frame():
    frame = picam2.capture_array()
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(rgb)
    img = img.resize((640, 480))
    imgtk = ImageTk.PhotoImage(image=img)
    video_label.imgtk = imgtk
    video_label.configure(image=imgtk)
    window.after(10, update_frame)

def on_close():
    picam2.stop()
    window.destroy()

window.protocol("WM_DELETE_WINDOW", on_close)
update_frame()
window.mainloop()

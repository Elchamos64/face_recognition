import time
import requests
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from shutil import which
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import io
import mysql.connector

##############################
# Save image to dataset folder
##############################
def save_image_for_model(name, image_bytes):
    dataset_dir = Path("dataset") / name
    dataset_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = dataset_dir / f"{timestamp}.jpg"
    with open(filename, "wb") as f:
        f.write(image_bytes)
    print(f"[SAVE] Image saved to {filename}")

##############################
# Database Manager
##############################
class DatabaseManager:
    def __init__(self, host='localhost', user='root', password='Right1234', database='face_recognition_db'):
        self.cnx = mysql.connector.connect(host=host, user=user, password=password)
        self.cnx.autocommit = True
        self.cursor = self.cnx.cursor()
        self.database = database
        self.create_database()
        self.cnx.database = database
        self.create_tables()
    
    def create_database(self):
        self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
    
    def create_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS persons (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            occupation VARCHAR(255),
            age VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INT AUTO_INCREMENT PRIMARY KEY,
            person_id INT,
            filename VARCHAR(255),
            image LONGBLOB,
            timestamp DATETIME,
            FOREIGN KEY (person_id) REFERENCES persons(id)
        )""")

    def add_person(self, name, occupation, age):
        self.cursor.execute("SELECT id FROM persons WHERE name = %s", (name,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        else:
            self.cursor.execute("INSERT INTO persons (name, occupation, age) VALUES (%s, %s, %s)", (name, occupation, age))
            return self.cursor.lastrowid
    
    def add_image(self, person_id, filename, image_data, timestamp):
        self.cursor.execute("INSERT INTO images (person_id, filename, image, timestamp) VALUES (%s, %s, %s, %s)", 
                            (person_id, filename, image_data, timestamp))
    
    def close(self):
        self.cursor.close()
        self.cnx.close()

##############################
# LinkedIn Scraper
##############################

class LinkedInScraper:
    def __init__(self, email, password, db_manager):
        self.email = email
        self.password = password
        self.db_manager = db_manager

        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1024,768')
        # comment this to view browser
        options.add_argument('--headless=new')  # "new" headless mode is required in latest Chromium

        # Force use of the system-installed chromedriver
        chromedriver_path = which("chromedriver")
        if not chromedriver_path:
            raise Exception("Chromedriver not found in PATH. Install it with `sudo apt install chromium-chromedriver`.")
        self.driver = webdriver.Chrome(service=ChromeService(executable_path=chromedriver_path), options=options)

    
    def login(self):
        print("Logging into LinkedIn...")
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        self.driver.find_element(By.ID, "username").send_keys(self.email)
        self.driver.find_element(By.ID, "password").send_keys(self.password + Keys.RETURN)
        time.sleep(3)
        print("Logged in.")

    def scrape_profile(self, profile_url):
        print(f"Scraping profile: {profile_url}")
        self.driver.get(profile_url)
        time.sleep(3)
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        name = "Unknown"
        name_tag = soup.find('h1')
        if name_tag and name_tag.get_text(strip=True):
            name = name_tag.get_text(strip=True)
        else:
            try:
                name_elem = self.driver.find_element(By.XPATH, "//h1[contains(@class,'text-heading')]")
                name = name_elem.text.strip()
            except:
                pass

        occupation_tag = soup.find('div', {'class': 'text-body-medium'})
        occupation = occupation_tag.get_text(strip=True)[:33] if occupation_tag else "Unknown"

        age = 23  # Not available on LinkedIn

        img_tag = soup.find('img', {'class': 'profile-photo-edit__preview'})
        image_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None
        image_bytes = None
        if image_url:
            try:
                response = requests.get(image_url)
                if response.status_code == 200:
                    image_bytes = response.content
            except Exception as e:
                print(f"[ERROR] Downloading image: {e}")
        return name, occupation, age, image_bytes

    def scrape_and_store(self, profile_urls):
        for url in profile_urls:
            name, occupation, age, image_bytes = self.scrape_profile(url)
            if not image_bytes:
                print(f"Skipping {name} due to missing image.")
                continue
            root = tk.Tk()
            app = ProfileReviewer(root, name, occupation, age, image_bytes, self.db_manager)
            root.mainloop()

    def close(self):
        self.driver.quit()

##############################
# Tkinter UI to Confirm Profile Info
##############################
class ProfileReviewer:
    def __init__(self, root, name, occupation, age, image_bytes, db_manager):
        self.root = root
        self.name = name
        self.occupation = occupation
        self.age = age
        self.image_bytes = image_bytes
        self.db_manager = db_manager

        self.root.title("Confirm Profile Info")

        tk.Label(root, text="Name:").grid(row=0, column=0, sticky="e")
        self.name_entry = tk.Entry(root, width=40)
        self.name_entry.insert(0, name)
        self.name_entry.grid(row=0, column=1)

        tk.Label(root, text="Occupation:").grid(row=1, column=0, sticky="e")
        self.occupation_entry = tk.Entry(root, width=40)
        self.occupation_entry.insert(0, occupation)
        self.occupation_entry.grid(row=1, column=1)

        tk.Label(root, text="Age:").grid(row=2, column=0, sticky="e")
        self.age_entry = tk.Entry(root, width=40)
        self.age_entry.insert(0, age)
        self.age_entry.grid(row=2, column=1)

        img = Image.open(io.BytesIO(image_bytes))
        img = img.resize((150, 150))
        self.tk_image = ImageTk.PhotoImage(img)
        tk.Label(root, image=self.tk_image).grid(row=0, column=2, rowspan=3, padx=10, pady=5)

        self.add_button = tk.Button(root, text="Add", command=self.on_add)
        self.add_button.grid(row=3, column=1, pady=10)

    def on_add(self):
        name = self.name_entry.get().strip()
        occupation = self.occupation_entry.get().strip()
        age = self.age_entry.get().strip()

        if not name or not occupation:
            messagebox.showerror("Invalid Data", "Name and occupation cannot be empty.")
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = f"{name}_{timestamp}.jpg"
        person_id = self.db_manager.add_person(name, occupation, age)
        self.db_manager.add_image(person_id, filename, self.image_bytes, timestamp)

        # Save image to filesystem for model training
        save_image_for_model(name, self.image_bytes)

        messagebox.showinfo("Success", f"{name} added to database.")
        self.root.destroy()

##############################
# Profile Entry UI (Startup)
##############################
class ProfileEntryUI:
    def __init__(self, master, on_submit):
        self.master = master
        self.on_submit = on_submit
        self.master.title("LinkedIn Scraper Setup")
        self.urls = []

        tk.Label(master, text="Enter LinkedIn Profile URL:").grid(row=0, column=0, sticky="w")
        self.url_entry = tk.Entry(master, width=60)
        self.url_entry.grid(row=1, column=0, padx=5)

        self.add_button = tk.Button(master, text="Add URL", command=self.add_url)
        self.add_button.grid(row=1, column=1, padx=5)

        self.url_listbox = tk.Listbox(master, width=80, height=8)
        self.url_listbox.grid(row=2, column=0, columnspan=2, pady=5)

        self.start_button = tk.Button(master, text="Start Scraping", command=self.start_scraping)
        self.start_button.grid(row=3, column=0, columnspan=2, pady=10)

    def add_url(self):
        url = self.url_entry.get().strip()
        if url and url.startswith("https://www.linkedin.com/in/"):
            self.urls.append(url)
            self.url_listbox.insert(tk.END, url)
            self.url_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Invalid URL", "Please enter a valid LinkedIn profile URL.")

    def start_scraping(self):
        if not self.urls:
            messagebox.showwarning("No URLs", "Add at least one profile URL before continuing.")
            return
        self.master.destroy()
        self.on_submit(self.urls)

##############################
# Main Execution
##############################
def main():
    email = "supermanismebvo123@gmail.com"
    password = ""

    db_manager = DatabaseManager(host='localhost', user='root', password='Right1234', database='face_recognition_db')
    scraper = LinkedInScraper(email, password, db_manager)

    def start_scraper_with_urls(urls):
        try:
            scraper.login()
            scraper.scrape_and_store(urls)
        finally:
            scraper.close()
            db_manager.close()

    root = tk.Tk()
    ProfileEntryUI(root, start_scraper_with_urls)
    root.mainloop()

if __name__ == "__main__":
    main()

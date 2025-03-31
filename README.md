# Face Recognition - Embedded Systems Project
## Overview
## Project Setup
1. Clone or Download the repository
    - You will need to place the following files in the same folder: facial_recognition.py, facial_recognition_hardware, image_capture.py and model_training.py

2. Create a Virtual Enviroment and Install Dependencies

    To create a virtual environment, open a new terminal window and type in:
    
    python3 -m venv --system-site-packages face_rec
    
    This will create a new virtual environment called "face_rec". You can find the folder of this virtual environment under home/pi and it will be called "face_rec".
    
    After creating the venv, enter into it by typing in:
    
    source face_rec/bin/activate
    
    Once your venv is active, install the following dependencies

      - OpenCV 
      - Imutils
      - CMake
      - pyttsx3
      - facial-recognition library

 
#3. Configuration
    - Replace Y_AP_TOKEN in the code with your actual API_TOKEN.
    - Optionally ajest the TESTING_MODEE, COLWEND, and other configuration variables as needed.
    - Ensure that your Rassber P is configured with the correct camera interface and Bluetooth Headsettings.

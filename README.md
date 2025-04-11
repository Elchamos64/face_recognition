# AI Face Rcognition - Oscar Ramos & Bryant Van Orden
## Overview
## Project Setup
1. Clone or Download the repository
   All you need to run this project if the `main.py` file

2. Create a Virtual Enviroment and Install Dependencies

    To create a virtual environment, open a new terminal window and type in:
    
    python3 -m venv --system-site-packages face_rec
    
    This will create a new virtual environment called "face_rec". You can find the folder of this virtual environment under home/pi and it will be called "face_rec".
    
    After creating the venv, enter into it by typing in:
    
    source face_rec/bin/activate
    
    Once your venv is active, install all the dependencies, you can view the main file to see what depencies you need.
 
3. How it works
   On the left side of the screen you will see 4 options in the UI. "Capture" , "Train" , "Recognize" and "Search". To be able to start recognizing faces you will first need to start building the database. To do       this, you can either use the built it web scrapper or the cature mode to take picture. To use the web scrapper you will have to change th variable in your code that holds you linkedin information. Once you have     entered that information you can now go to the "search" tab and enter the url of the linkedin profile you want to search. It will return their name and occupation, and you can add the correct age (defaulted to      23). Once the web scrapper has found the correct person click "add", this will add that person to the SQL database. Next thing you want to do is go to the "train" tab and hit "train model" this well make the        person's data available to the AI so it can be trained to recognize that face and all other faces stored in the database. Once that is done, you can run the recognize tab and see the magic happen.


4. Note that this project is meant to run on a Rapsberry Pi 5:
   For this project we used: Raspberry Pi 5, AI Hat Accelerator, AI Camera module (you can use a webcam and it will work just as good)

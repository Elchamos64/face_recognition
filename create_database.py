import mysql.connector
from mysql.connector import Error

def create_database_and_tables(host, user, password, database):
    try:
        # Connect to MySQL server (without specifying a database)
        cnx = mysql.connector.connect(host=host, user=user, password=password)
    except Error as err:
        print(f"Error connecting to MySQL: {err}")
        print("Make sure your MySQL server is running and accessible on localhost:3306.")
        return

    cursor = cnx.cursor()
    try:
        # Create the database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
        print(f"Database '{database}' created or already exists.")
        
        # Connect to the newly created database
        cnx.database = database

        # Create 'persons' table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS persons (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            occupation VARCHAR(255),
            age INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("Table 'persons' created or already exists.")

        # Create 'images' table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INT AUTO_INCREMENT PRIMARY KEY,
            person_id INT,
            filename VARCHAR(255),
            image LONGBLOB,
            timestamp DATETIME,
            FOREIGN KEY (person_id) REFERENCES persons(id)
        )
        """)
        print("Table 'images' created or already exists.")

        # Create 'encodings' table for storing model data
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS encodings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            data LONGBLOB,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """)
        print("Table 'encodings' created or already exists.")
    except Error as err:
        print(f"Error creating tables: {err}")
    finally:
        cursor.close()
        cnx.close()
        print("Database setup complete.")

if __name__ == '__main__':
    # Set your MySQL connection parameters here
    host = 'localhost'
    user = 'root'
    password = 'Right1234'  # Update with your MySQL password if needed
    database = 'face_recognition_db'
    
    create_database_and_tables(host, user, password, database)

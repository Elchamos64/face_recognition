import mysql.connector
from mysql.connector import Error

def clear_all_tables(host, user, password, database):
    try:
        cnx = mysql.connector.connect(host=host, user=user, password=password, database=database)
        cursor = cnx.cursor()

        # Disable foreign key checks to avoid constraint errors during truncation
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

        # List of tables to clear
        tables = ['images', 'encodings', 'persons']  # Order matters due to foreign key dependencies

        for table in tables:
            cursor.execute(f"TRUNCATE TABLE {table}")
            print(f"Table '{table}' has been cleared.")

        # Re-enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        cnx.commit()
    except Error as err:
        print(f"Error clearing tables: {err}")
    finally:
        cursor.close()
        cnx.close()
        print("All tables have been cleared.")

if __name__ == '__main__':
    host = 'localhost'
    user = 'root'
    password = 'Right1234'
    database = 'face_recognition_db'

    clear_all_tables(host, user, password, database)

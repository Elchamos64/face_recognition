import mysql.connector

mysql.connector.connect(
    host='localhost',
    user='root',
    password='Right1234',
    unix_socket='/var/run/mysqld/mysqld.sock'
)

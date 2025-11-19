import mysql.connector

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Aa822010@",   # if you have a MySQL password, put it here
            database="waste_mgmt"   # your actual database name
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None
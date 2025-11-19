import mysql.connector
from db_config import get_db_connection

def register_flow():
    print("\n--- Register ---")
    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO users (username, password_hash)
            VALUES (%s, %s)
        """, (username, password))

        conn.commit()
        print("Registration successful!")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        conn.close()


def login_flow():
    print("\n--- Login ---")
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT user_id, username 
        FROM users 
        WHERE username = %s AND password_hash = %s
    """, (username, password))

    row = cur.fetchone()
    conn.close()

    if row:
        print("Login successful!")
        return {"id": row[0], "username": row[1]}
    else:
        print("Invalid username or password.")
        return None
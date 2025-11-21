import mysql.connector
from db_config import get_db_connection

def register_flow():
    """
    Handles the user registration process.
    Prompts for username and password, then inserts into the database.
    """
    print("\n--- Register ---")
    username = input("Choose a username: ").strip()
    password = input("Choose a password: ").strip()

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Insert new user into the users table
        cur.execute("""
            INSERT INTO users (username, password_hash)
            VALUES (%s, %s)
        """, (username, password))

        conn.commit()
        print(f"Registration successful! Welcome, {username}.")
    except mysql.connector.Error as err:
        print(f"Registration failed: {err}")
    finally:
        conn.close()

def login_flow():
    """
    Handles the user login process.
    Prompts for username and password, then checks credentials.
    Returns user info dict if successful, else None.
    """
    print("\n--- Login ---")
    username = input("Enter your username: ").strip()
    password = input("Enter your password: ").strip()

    conn = get_db_connection()
    cur = conn.cursor()

    # Query for user with matching credentials
    cur.execute("""
        SELECT user_id, username 
        FROM users 
        WHERE username = %s AND password_hash = %s
    """, (username, password))

    user_row = cur.fetchone()
    conn.close()

    if user_row:
        print(f"Login successful! Welcome back, {user_row[1]}.")
        return {"id": user_row[0], "username": user_row[1]}
    else:
        print("Invalid username or password. Please try again.")
        return None
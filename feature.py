import mysql.connector
from db_config import get_db_connection
from datetime import datetime

# Auto category detection (simple logic)
def categorise_waste(description: str) -> str:
    desc = description.lower()
    if "plastic" in desc:
        return "plastic"
    elif "paper" in desc:
        return "paper"
    elif "glass" in desc:
        return "glass"
    elif "food" in desc or "organic" in desc:
        return "organic"
    return "mixed"


# ------------------------------------------------------
# CREATE PICKUP REQUEST
# ------------------------------------------------------
def create_pickup_request(user_id, items, address, sched_datetime):
    conn = get_db_connection()
    if not conn:
        return {"success": False, "error": "Database connection failed"}

    cur = conn.cursor()

    mysql_date = sched_datetime.strftime("%Y-%m-%d %H:%M:%S")
    category = categorise_waste(items)

    try:
        cur.execute("""
            INSERT INTO pickup_requests 
            (user_id, items, pickup_address, pickup_date, category, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, items, address, mysql_date, category, "scheduled"))

        conn.commit()

        # Fetch inserted row
        cur.execute("SELECT * FROM pickup_requests WHERE request_id = LAST_INSERT_ID()")
        row = cur.fetchone()

        return {"success": True, "request": row}

    except mysql.connector.Error as err:
        return {"success": False, "error": str(err)}

    finally:
        conn.close()


# ------------------------------------------------------
# GET USER REQUESTS  (FIXED – NO INDEX ERROR)
# ------------------------------------------------------
def get_requests_for_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT request_id, category, pickup_address, pickup_date,
               items, status, picked_at, reported_wrong
        FROM pickup_requests
        WHERE user_id=%s
        ORDER BY pickup_date DESC
    """, (user_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# ------------------------------------------------------
# UPDATE STATUS (ADMIN)
# ------------------------------------------------------
def update_request_status(request_id, new_status, picked_at=None, report_wrong=False):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        if new_status == "picked":
            if picked_at:
                picked = picked_at.strftime("%Y-%m-%d %H:%M:%S")
            else:
                picked = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cur.execute("""
                UPDATE pickup_requests 
                SET status=%s, picked_at=%s, reported_wrong=%s
                WHERE request_id=%s
            """, ("picked", picked, report_wrong, request_id))

        else:
            cur.execute("""
                UPDATE pickup_requests 
                SET status=%s 
                WHERE request_id=%s
            """, (new_status, request_id))

        conn.commit()
        return {"success": True}

    except Exception as e:
        return {"success": False, "error": str(e)}

    finally:
        conn.close()


# ------------------------------------------------------
# GET FINES
# ------------------------------------------------------
def get_fines_for_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT fine_id, request_id, amount, reason, fine_date, paid
        FROM fines_log
        WHERE user_id=%s
        ORDER BY fine_date DESC
    """, (user_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# ------------------------------------------------------
# REPORT GENERATION
# ------------------------------------------------------
def generate_report(period="daily"):
    conn = get_db_connection()
    cur = conn.cursor()

    if period == "daily":
        cur.execute("SELECT COUNT(*), SUM(amount) FROM fines_log WHERE DATE(fine_date) = CURDATE()")
    else:
        cur.execute("SELECT COUNT(*), SUM(amount) FROM fines_log WHERE fine_date >= NOW() - INTERVAL 7 DAY")

    data = cur.fetchone()
    cur.close()
    conn.close()

    return {
        "period": period,
        "total_fines": data[1],
        "count": data[0]
    }
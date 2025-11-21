import mysql.connector
from db_config import get_db_connection
from datetime import datetime
def categorise_waste(description: str) -> str:
    """
    Categorizes the waste based on keywords in the description.
    Returns a string category.
    """
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
def create_pickup_request(user_id, items, address, sched_datetime):
    """
    Creates a new pickup request for the user.
    Returns a dict with success status and request row or error.
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "error": "Database connection failed"}
    cur = conn.cursor()
    mysql_date = sched_datetime.strftime("%Y-%m-%d %H:%M:%S")
    category = categorise_waste(items)
    try:
        # Insert the pickup request into the database
        cur.execute("""
            INSERT INTO pickup_requests 
            (user_id, items, pickup_address, pickup_date, category, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, items, address, mysql_date, category, "scheduled"))
        conn.commit()
        # Retrieve the newly created request
        cur.execute("SELECT * FROM pickup_requests WHERE request_id = LAST_INSERT_ID()")
        row = cur.fetchone()
        return {"success": True, "request": row}
    except mysql.connector.Error as err:
        return {"success": False, "error": str(err)}
    finally:
        conn.close()
def get_requests_for_user(user_id):
    """
    Retrieves all pickup requests for a given user, ordered by date.
    Returns a list of request rows.
    """
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
def update_request_status(request_id, new_status, picked_at=None, report_wrong=False):
    """
    Updates the status of a pickup request.
    If status is 'picked', also updates picked_at and reported_wrong fields.
    Returns a dict with success status or error.
    """
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
def get_fines_for_user(user_id):
    """
    Retrieves all fines for a given user, ordered by date.
    Returns a list of fine rows.
    """
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
def generate_report(period="daily"):
    """
    Generates a report of fines for the given period (daily or weekly).
    Returns a dict with period, total fines amount, and count.
    """
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
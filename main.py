# main.py - CLI runner for the system (fixed)
from login_register import register_flow, login_flow
import feature
from datetime import datetime, timedelta, timezone

def print_menu():
    print('''
--- Waste Management System ---
1) Register
2) Login
3) Exit
''')

def user_menu():
    print('''
--- User Menu ---
1) Create pickup request
2) View my requests
3) Update request status (admin-style)
4) View my fines
5) Generate daily report (admin)
6) Generate weekly report (admin)
7) Logout
''')

def run():
    print("Welcome to the City Waste Management System (CLI demo).")
    while True:
        print_menu()
        choice = input("Choose: ").strip()
        if choice == "1":
            register_flow()
        elif choice == "2":
            user = login_flow()
            if user:
                user_loop(user)
        elif choice == "3":
            print("Bye.")
            break
        else:
            print("Invalid choice.")

def user_loop(user):
    while True:
        user_menu()
        c = input("Choose: ").strip()
        if c == "1":
            item = input("Describe the waste items (e.g. '3 plastic bottles'): ").strip()
            address = input("Pickup address: ").strip()
            date_str = input("Preferred pickup date (YYYY-MM-DD) or leave blank for tomorrow: ").strip()

            # Use timezone-aware datetime to avoid DeprecationWarning
            if not date_str:
                sched = datetime.now(timezone.utc) + timedelta(days=1)
            else:
                try:
                    # fromisoformat supports YYYY-MM-DD and YYYY-MM-DDTHH:MM:SS
                    # ensure we attach UTC if user entered only a date
                    tmp = datetime.fromisoformat(date_str)
                    if tmp.tzinfo is None:
                        # treat as local naive datetime -> convert to UTC-aware at midnight
                        sched = datetime(tmp.year, tmp.month, tmp.day, tzinfo=timezone.utc)
                    else:
                        sched = tmp.astimezone(timezone.utc)
                except Exception:
                    print("Invalid date format, using tomorrow.")
                    sched = datetime.now(timezone.utc) + timedelta(days=1)

            res = feature.create_pickup_request(user['id'], item, address, sched)

            # feature.create_pickup_request returns dict {"success": True/False, "request": row}
            if res.get("success"):
                row = res.get("request")
                if isinstance(row, (list, tuple)):
                    # row may be SELECT * or a specific SELECT order depending on your feature.py / DB schema
                    rid = row[0] if len(row) > 0 else "(unknown)"
                    # attempt to fetch category from likely indices (many schemas put category around index 5)
                    category = None
                    if len(row) >= 6:
                        category = row[5]
                    # fallback: try to find a known category string inside the tuple
                    if not category:
                        for v in row:
                            if isinstance(v, str) and v.lower() in ('plastic','paper','glass','organic','mixed','metal','hazardous'):
                                category = v
                                break
                    print(f"Pickup request created (id={rid}). Category detected: {category}")
                else:
                    # if feature returned something else
                    print("Pickup request created. (created row returned in unexpected format)", row)
            else:
                print("Could not create request.", res.get("error", res))

        elif c == "2":
            rows = feature.get_requests_for_user(user['id'])
            if not rows:
                print("No requests yet.")
            else:
                for r in rows:
                    # Be defensive about the tuple shape
                    # Expected shape from feature.get_requests_for_user (final version): 
                    # (request_id, category, pickup_address, pickup_date, items, status, picked_at, reported_wrong)
                    try:
                        if isinstance(r, (list, tuple)):
                            if len(r) >= 8:
                                print("ID:", r[0], "| Category:", r[1], "| Address:", r[2],
                                      "| Scheduled:", r[3], "| Items:", r[4], "| Status:", r[5],
                                      "| Picked at:", r[6], "| Reported wrong:", bool(r[7]))
                            elif len(r) >= 6:
                                # fallback ordering: request_id, items, pickup_address, pickup_date, category, status
                                print("ID:", r[0], "| Category:", r[4] if len(r) > 4 else r[1],
                                      "| Address:", r[2] if len(r) > 2 else "(unknown)",
                                      "| Scheduled:", r[3] if len(r) > 3 else "(unknown)",
                                      "| Status:", r[5] if len(r) > 5 else "(unknown)")
                            else:
                                print("ROW:", r)
                        else:
                            print("ROW (unexpected type):", r)
                    except Exception as e:
                        print("Error printing row:", e, "raw:", r)

        elif c == "3":
            print("(This is an admin-style action in this demo.)")
            try:
                rid = int(input("Request ID to update: ").strip())
            except ValueError:
                print("Invalid ID.")
                continue

            print("New status options: picked / canceled / reported_wrong / scheduled")
            new_status = input("New status: ").strip()
            if new_status == "picked":
                # optionally enter actual picked datetime
                date_s = input("Picked at (YYYY-MM-DD HH:MM) or leave blank for now: ").strip()
                if date_s:
                    try:
                        picked_dt = datetime.fromisoformat(date_s)
                        if picked_dt.tzinfo is None:
                            picked_dt = picked_dt.replace(tzinfo=timezone.utc)
                    except Exception:
                        picked_dt = None
                else:
                    picked_dt = None
                report_wrong = input("Report wrong handling? (y/n): ").strip().lower() == "y"
                res = feature.update_request_status(rid, "picked", picked_at=picked_dt, report_wrong=report_wrong)
                print(res)
            else:
                res = feature.update_request_status(rid, new_status)
                print(res)

        elif c == "4":
            fines = feature.get_fines_for_user(user['id'])
            if not fines:
                print("No fines.")
            else:
                for f in fines:
                    # expected: fine_id, request_id, amount, reason, fine_date, paid
                    if isinstance(f, (list, tuple)) and len(f) >= 6:
                        print("Fine ID:", f[0], "| Request:", f[1], "| Amount:", f[2], "| Reason:", f[3], "| Date:", f[4], "| Paid:", bool(f[5]))
                    else:
                        print("Fine row:", f)

        elif c == "5":
            rpt = feature.generate_report("daily")
            print_report(rpt)

        elif c == "6":
            rpt = feature.generate_report("weekly")
            print_report(rpt)

        elif c == "7":
            print("Logging out.")
            break

        else:
            print("Invalid option.")

def print_report(rpt):
    if not rpt:
        print("Empty report.")
        return

    # Accept multiple possible report shapes
    if isinstance(rpt, dict):
        # New compact shape returned by feature.generate_report
        if 'period' in rpt and ('total_fines' in rpt or 'count' in rpt):
            print(f"\nReport ({rpt.get('period')})")
            print("Total fines:", rpt.get('total_fines'))
            print("Count:", rpt.get('count'))
            print("----\n")
            return

        # Old/UI-rich shape
        if all(k in rpt for k in ('period_start','total_requests')):
            print(f"\nReport starting {rpt.get('period_start')}")
            print("Total requests:", rpt.get('total_requests'))
            print("Picked:", rpt.get('picked'))
            print("Pending:", rpt.get('pending'))
            print("Fines count:", rpt.get('fines_count'))
            print("Fines total amount:", rpt.get('fines_total_amount'))
            print("Top categories:")
            for cat, cnt in rpt.get('top_categories', []):
                print(f"  {cat}: {cnt}")
            print("----\n")
            return

    # Fallback: just print raw
    print("Report output (raw):", rpt)

if __name__ == "__main__":
    run()
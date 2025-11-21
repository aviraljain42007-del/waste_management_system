from login_register import register_flow, login_flow
import feature
from datetime import datetime, timedelta, timezone

def print_menu():
    # Main menu for the application
    print('''
--- City Waste Management System ---
1) Register (Create a new account)
2) Login (Access your account)
3) Exit
''')

def user_menu():
    # Menu shown after user logs in
    print('''
--- User Menu ---
1) Create a new pickup request
2) View my pickup requests
3) Update request status (admin/demo)
4) View my fines
5) Generate daily report (admin)
6) Generate weekly report (admin)
7) Logout
''')

def run():
    print("Welcome to the City Waste Management System (CLI demo).\n")
    while True:
        print_menu()
        choice = input("Enter your choice (1-3): ").strip()
        if choice == "1":
            register_flow()
        elif choice == "2":
            user = login_flow()
            if user:
                user_loop(user)
        elif choice == "3":
            print("Thank you for using the system. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

def user_loop(user):
    while True:
        user_menu()
        user_choice = input("Enter your choice (1-7): ").strip()

        if user_choice == "1":
            # Create a new pickup request
            waste_description = input("Describe the waste items (e.g. '3 plastic bottles'): ").strip()
            pickup_address = input("Enter the pickup address: ").strip()
            date_input = input("Preferred pickup date (YYYY-MM-DD) or leave blank for tomorrow: ").strip()
            if not date_input:
                scheduled_date = datetime.now(timezone.utc) + timedelta(days=1)
            else:
                try:
                    tmp = datetime.fromisoformat(date_input)
                    if tmp.tzinfo is None:
                        scheduled_date = datetime(tmp.year, tmp.month, tmp.day, tzinfo=timezone.utc)
                    else:
                        scheduled_date = tmp.astimezone(timezone.utc)
                except Exception:
                    print("Invalid date format, using tomorrow.")
                    scheduled_date = datetime.now(timezone.utc) + timedelta(days=1)

            result = feature.create_pickup_request(user['id'], waste_description, pickup_address, scheduled_date)
            if result.get("success"):
                row = result.get("request")
                if isinstance(row, (list, tuple)):
                    request_id = row[0] if len(row) > 0 else "(unknown)"
                    category = None
                    if len(row) >= 6:
                        category = row[5]
                    if not category:
                        for v in row:
                            if isinstance(v, str) and v.lower() in ('plastic','paper','glass','organic','mixed','metal','hazardous'):
                                category = v
                                break
                    print(f"Pickup request created (ID={request_id}). Category detected: {category}")
                else:
                    print("Pickup request created. (Unexpected row format)", row)
            else:
                print("Could not create request.", result.get("error", result))

        elif user_choice == "2":
            # View user's pickup requests
            requests = feature.get_requests_for_user(user['id'])
            if not requests:
                print("No pickup requests found.")
            else:
                for req in requests:
                    try:
                        if isinstance(req, (list, tuple)):
                            if len(req) >= 8:
                                print("ID:", req[0], "| Category:", req[1], "| Address:", req[2],
                                      "| Scheduled:", req[3], "| Items:", req[4], "| Status:", req[5],
                                      "| Picked at:", req[6], "| Reported wrong:", bool(req[7]))
                            elif len(req) >= 6:
                                print("ID:", req[0], "| Category:", req[4] if len(req) > 4 else req[1],
                                      "| Address:", req[2] if len(req) > 2 else "(unknown)",
                                      "| Scheduled:", req[3] if len(req) > 3 else "(unknown)",
                                      "| Status:", req[5] if len(req) > 5 else "(unknown)")
                            else:
                                print("ROW:", req)
                        else:
                            print("ROW (unexpected type):", req)
                    except Exception as e:
                        print("Error displaying request:", e, "raw:", req)

        elif user_choice == "3":
            # Update request status (admin/demo)
            print("(This is an admin-style action in this demo.)")
            try:
                request_id = int(input("Enter the Request ID to update: ").strip())
            except ValueError:
                print("Invalid ID. Please enter a numeric value.")
                continue

            print("Status options: picked / canceled / reported_wrong / scheduled")
            new_status = input("Enter new status: ").strip()
            if new_status == "picked":
                picked_at_input = input("Picked at (YYYY-MM-DD HH:MM) or leave blank for now: ").strip()
                if picked_at_input:
                    try:
                        picked_dt = datetime.fromisoformat(picked_at_input)
                        if picked_dt.tzinfo is None:
                            picked_dt = picked_dt.replace(tzinfo=timezone.utc)
                    except Exception:
                        picked_dt = None
                else:
                    picked_dt = None
                report_wrong = input("Report wrong handling? (y/n): ").strip().lower() == "y"
                result = feature.update_request_status(request_id, "picked", picked_at=picked_dt, report_wrong=report_wrong)
                print(result)
            else:
                result = feature.update_request_status(request_id, new_status)
                print(result)

        elif user_choice == "4":
            # View user's fines
            fines = feature.get_fines_for_user(user['id'])
            if not fines:
                print("No fines found.")
            else:
                for fine in fines:
                    if isinstance(fine, (list, tuple)) and len(fine) >= 6:
                        print("Fine ID:", fine[0], "| Request:", fine[1], "| Amount:", fine[2], "| Reason:", fine[3], "| Date:", fine[4], "| Paid:", bool(fine[5]))
                    else:
                        print("Fine row:", fine)

        elif user_choice == "5":
            # Generate daily report (admin)
            report = feature.generate_report("daily")
            print_report(report)

        elif user_choice == "6":
            # Generate weekly report (admin)
            report = feature.generate_report("weekly")
            print_report(report)

        elif user_choice == "7":
            print("Logging out. Returning to main menu.\n")
            break

        else:
            print("Invalid option. Please enter a number between 1 and 7.")

def print_report(rpt):
    # Nicely print the report data
    if not rpt:
        print("No data available for this report.")
        return
    if isinstance(rpt, dict):
        if 'period' in rpt and ('total_fines' in rpt or 'count' in rpt):
            print(f"\nReport for period: {rpt.get('period')}")
            print("Total fines:", rpt.get('total_fines'))
            print("Total requests:", rpt.get('count'))
            print("----\n")
            return
        if all(k in rpt for k in ('period_start','total_requests')):
            print(f"\nReport starting {rpt.get('period_start')}")
            print("Total requests:", rpt.get('total_requests'))
            print("Picked up:", rpt.get('picked'))
            print("Pending:", rpt.get('pending'))
            print("Fines issued:", rpt.get('fines_count'))
            print("Total fines amount:", rpt.get('fines_total_amount'))
            print("Top waste categories:")
            for cat, cnt in rpt.get('top_categories', []):
                print(f"  {cat}: {cnt}")
            print("----\n")
            return
    print("Report output (raw):", rpt)

if __name__ == "__main__":
    run()
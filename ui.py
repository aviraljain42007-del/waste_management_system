# ui.py
import tkinter as tk
from tkinter import messagebox, simpledialog
from login_register import register_flow, login_flow
import feature
from datetime import datetime, timedelta

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Waste Management System")
        self.root.geometry("380x380")
        self.user = None
        self.build_login_register()

    def build_login_register(self):
        # Clear root
        for w in self.root.winfo_children():
            w.destroy()

        frm = tk.Frame(self.root, padx=12, pady=12)
        frm.pack(expand=True, fill=tk.BOTH)

        tk.Label(frm, text="Login / Register", font=("Helvetica", 16, "bold")).pack(pady=(0,10))

        tk.Label(frm, text="Username:").pack(anchor="w")
        self.username_var = tk.StringVar()
        tk.Entry(frm, textvariable=self.username_var).pack(fill="x")

        tk.Label(frm, text="Password:").pack(anchor="w", pady=(8,0))
        self.password_var = tk.StringVar()
        tk.Entry(frm, textvariable=self.password_var, show="*").pack(fill="x")

        tk.Button(frm, text="Login", width=15, command=self.do_login).pack(pady=(14,5))
        tk.Button(frm, text="Register", width=15, command=self.do_register).pack()

    def do_register(self):
        u = self.username_var.get().strip()
        p = self.password_var.get().strip()
        if not u or not p:
            messagebox.showwarning("Input", "Username and password required.")
            return
        res = register_flow(u, p)
        if res.get("success"):
            messagebox.showinfo("Success", "Registered successfully. You may login now.")
        else:
            messagebox.showerror("Error", f"Registration failed: {res.get('error')}")

    def do_login(self):
        u = self.username_var.get().strip()
        p = self.password_var.get().strip()
        if not u or not p:
            messagebox.showwarning("Input", "Username and password required.")
            return
        user = login_flow(u, p)
        if user:
            self.user = user
            messagebox.showinfo("Success", f"Login successful. Welcome {user['username']}.")
            self.build_dashboard()
        else:
            messagebox.showerror("Error", "Invalid login.")

    # ---------------- Dashboard (after login) ----------------
    def build_dashboard(self):
        for w in self.root.winfo_children():
            w.destroy()

        frm = tk.Frame(self.root, padx=12, pady=12)
        frm.pack(expand=True, fill=tk.BOTH)

        tk.Label(frm, text=f"Welcome — {self.user['username']}", font=("Helvetica", 14, "bold")).pack(pady=(0,8))

        # User actions
        tk.Button(frm, text="Create Pickup Request", width=25, command=self.open_create_request).pack(pady=6)
        tk.Button(frm, text="View My Requests", width=25, command=self.view_requests).pack(pady=6)
        tk.Button(frm, text="View My Fines", width=25, command=self.view_fines).pack(pady=6)
        tk.Button(frm, text="Generate Daily Report (admin)", width=25, command=lambda: self.generate_report("daily")).pack(pady=6)
        tk.Button(frm, text="Generate Weekly Report (admin)", width=25, command=lambda: self.generate_report("weekly")).pack(pady=6)
        tk.Button(frm, text="Logout", width=25, command=self.logout).pack(pady=10)

        self.output_txt = tk.Text(frm, height=8, wrap=tk.WORD)
        self.output_txt.pack(fill="both", expand=True, pady=(8,0))

    def logout(self):
        self.user = None
        self.build_login_register()

    # ---- Create pickup request UI ----
    def open_create_request(self):
        d = tk.Toplevel(self.root)
        d.title("Create Pickup Request")
        d.geometry("360x300")
        frm = tk.Frame(d, padx=10, pady=10)
        frm.pack(fill="both", expand=True)

        tk.Label(frm, text="Describe items (e.g. '3 plastic bottles')").pack(anchor="w")
        items_var = tk.StringVar()
        tk.Entry(frm, textvariable=items_var).pack(fill="x")

        tk.Label(frm, text="Pickup address").pack(anchor="w", pady=(8,0))
        addr_var = tk.StringVar()
        tk.Entry(frm, textvariable=addr_var).pack(fill="x")

        tk.Label(frm, text="Pickup date & time (YYYY-MM-DD HH:MM) or leave blank for tomorrow").pack(anchor="w", pady=(8,0))
        dt_var = tk.StringVar()
        dt_var.set("")  # default blank -> tomorrow
        tk.Entry(frm, textvariable=dt_var).pack(fill="x")

        def submit():
            items = items_var.get().strip()
            addr = addr_var.get().strip()
            date_s = dt_var.get().strip()
            if not items or not addr:
                messagebox.showwarning("Input", "Items and address required.")
                return
            if not date_s:
                sched = datetime.utcnow() + timedelta(days=1)
            else:
                try:
                    sched = datetime.strptime(date_s, "%Y-%m-%d %H:%M")
                except Exception:
                    messagebox.showerror("Input", "Invalid date format. Use YYYY-MM-DD HH:MM")
                    return
            resp = feature.create_pickup_request(self.user["user_id"], items, addr, sched)
            if resp.get("success"):
                messagebox.showinfo("Success", "Pickup request created.")
                d.destroy()
                self.output("Created: " + str(resp.get("request")))
            else:
                messagebox.showerror("Error", f"Could not create pickup: {resp.get('error')}")

        tk.Button(frm, text="Create", width=20, command=submit).pack(pady=12)

    def view_requests(self):
        rows = feature.get_requests_for_user(self.user["user_id"])
        if not rows:
            self.output("No requests found.")
            return
        text = "Your pickup requests:\n\n"
        for r in rows:
            text += f"ID:{r['request_id']} | items:{r['items']} | address:{r['pickup_address']} | pickup:{r['pickup_date']} | status:{r['status']}\n"
        self.output(text)

    def view_fines(self):
        rows = feature.get_fines_for_user(self.user["user_id"])
        if not rows:
            self.output("No fines found.")
            return
        text = "Your fines:\n\n"
        for r in rows:
            text += f"FineID:{r['fine_id']} | Request:{r['request_id']} | Amount:{r['amount']} | Reason:{r['reason']} | Date:{r['fine_date']}\n"
        self.output(text)

    def generate_report(self, period):
        res = feature.generate_report(period)
        if not res.get("success"):
            self.output("Report error: " + str(res.get("error")))
            return
        self.output(f"Report ({period}): count={res['count']}, total_fines={res['total_fines']}")

    def output(self, txt):
        self.output_txt.delete("1.0", tk.END)
        self.output_txt.insert(tk.END, txt)

def run_app():
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    run_app()

import tkinter as tk
from tkinter import messagebox, ttk
import sys, os, datetime, calendar
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.db_connection import get_connection

COLORS = {
    "main_bg":      "#F4F6F8",
    "white":        "#FFFFFF",
    "accent":       "#2980B9",
    "accent_dk":    "#2471A3",
    "text_dark":    "#2C3E50",
    "text_muted":   "#7F8C8D",
    "border":       "#DDE1E7",
    "success":      "#27AE60",
    "danger":       "#E74C3C",
    "warning":      "#E67E22",
    "input_bg":     "#FDFDFD",
    "label_bg":     "#F0F3F4",
    "row_alt":      "#F8FAFB",
    "present_bg":   "#EAFAF1",
    "absent_bg":    "#FDEDEC",
    "halfday_bg":   "#FEF9E7",
    "overtime_bg":  "#EBF5FB",
    "sidebar_bg":   "#1E2A3A",
}

def styled_btn(parent, text, command, color=None, fg="white", padx=14, pady=7):
    color = color or COLORS["accent"]
    return tk.Button(parent, text=text, command=command,
                     bg=color, fg=fg, font=("Segoe UI", 10, "bold"),
                     relief="flat", cursor="hand2", padx=padx, pady=pady,
                     activebackground=color, activeforeground=fg)

def styled_entry(parent, width=28):
    return tk.Entry(parent, width=width, font=("Segoe UI", 10),
                    bg=COLORS["input_bg"], fg=COLORS["text_dark"],
                    relief="flat", highlightthickness=1,
                    highlightbackground=COLORS["border"],
                    highlightcolor=COLORS["accent"],
                    insertbackground=COLORS["text_dark"])


# =============================================================================
#  STAFF FORM  (Add / Edit)
# =============================================================================

class StaffForm(tk.Toplevel):
    def __init__(self, parent, on_saved, staff_id=None):
        super().__init__(parent)
        self.on_saved  = on_saved
        self.staff_id  = staff_id
        self.title("Edit Staff Member" if staff_id else "Add Staff Member")
        self.geometry("560x700")
        self.resizable(False, False)
        self.configure(bg=COLORS["main_bg"])
        self.grab_set()
        self._build()
        if staff_id:
            self._load()

    def _build(self):
        color = COLORS["accent"] if self.staff_id else COLORS["success"]
        h = tk.Frame(self, bg=color, height=48)
        h.pack(fill="x"); h.pack_propagate(False)
        tk.Label(h, text="  Edit Staff Member" if self.staff_id else "  Add New Staff Member",
                 bg=color, fg="white",
                 font=("Segoe UI", 12, "bold")).pack(side="left", padx=16, pady=10)

        f = tk.Frame(self, bg=COLORS["main_bg"])
        f.pack(fill="both", expand=True, padx=24, pady=14)

        def lbl(text):
            tk.Label(f, text=text, bg=COLORS["main_bg"], fg=COLORS["text_dark"],
                     font=("Segoe UI", 10)).pack(anchor="w")

        lbl("Full Name *")
        self._name_e = styled_entry(f, width=38)
        self._name_e.pack(anchor="w", ipady=5, pady=(2,8), fill="x")

        lbl("Role / Position *")
        self._role_e = styled_entry(f, width=38)
        self._role_e.pack(anchor="w", ipady=5, pady=(2,8), fill="x")

        # Wage section
        wage_frame = tk.Frame(f, bg=COLORS["label_bg"],
                              highlightbackground=COLORS["border"], highlightthickness=1)
        wage_frame.pack(fill="x", pady=(0,8))
        tk.Label(wage_frame, text="  Wage Settings", bg=COLORS["label_bg"],
                 fg=COLORS["text_muted"], font=("Segoe UI", 9, "bold")).pack(anchor="w",
                 padx=8, pady=(6,4))

        wf = tk.Frame(wage_frame, bg=COLORS["label_bg"])
        wf.pack(fill="x", padx=8, pady=(0,8))

        # Row 1: Hourly wage
        r1 = tk.Frame(wf, bg=COLORS["label_bg"]); r1.pack(fill="x", pady=2)
        tk.Label(r1, text="Hourly Wage (Rs.) *", bg=COLORS["label_bg"],
                 fg=COLORS["text_dark"], font=("Segoe UI", 10),
                 width=22, anchor="w").pack(side="left")
        self._hourly_e = styled_entry(r1, width=14)
        self._hourly_e.pack(side="left", ipady=4)

        # Row 2: Standard hours
        r2 = tk.Frame(wf, bg=COLORS["label_bg"]); r2.pack(fill="x", pady=2)
        tk.Label(r2, text="Standard Hours/Day *", bg=COLORS["label_bg"],
                 fg=COLORS["text_dark"], font=("Segoe UI", 10),
                 width=22, anchor="w").pack(side="left")
        self._stdhours_e = styled_entry(r2, width=14)
        self._stdhours_e.insert(0, "8")
        self._stdhours_e.pack(side="left", ipady=4)

        # Row 3: Overtime rate
        r3 = tk.Frame(wf, bg=COLORS["label_bg"]); r3.pack(fill="x", pady=2)
        tk.Label(r3, text="Overtime Multiplier", bg=COLORS["label_bg"],
                 fg=COLORS["text_dark"], font=("Segoe UI", 10),
                 width=22, anchor="w").pack(side="left")
        self._otrate_e = styled_entry(r3, width=14)
        self._otrate_e.insert(0, "1.5")
        self._otrate_e.pack(side="left", ipady=4)
        tk.Label(r3, text="  e.g. 1.5 = 150% of hourly",
                 bg=COLORS["label_bg"], fg=COLORS["text_muted"],
                 font=("Segoe UI", 8)).pack(side="left", padx=4)

        lbl("Phone Number")
        self._phone_e = styled_entry(f, width=28)
        self._phone_e.pack(anchor="w", ipady=5, pady=(2,8))

        lbl("Address")
        self._addr_e = styled_entry(f, width=38)
        self._addr_e.pack(anchor="w", ipady=5, pady=(2,8), fill="x")

        lbl("Join Date")
        self._join_var = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        tk.Entry(f, textvariable=self._join_var, width=18,
                 font=("Segoe UI", 10), bg=COLORS["input_bg"],
                 fg=COLORS["text_dark"], relief="flat",
                 highlightthickness=1, highlightbackground=COLORS["border"]
                 ).pack(anchor="w", ipady=5, pady=(2,8))

        lbl("Status")
        self._status_var = tk.StringVar(value="active")
        ttk.Combobox(f, textvariable=self._status_var,
                     values=["active", "inactive"],
                     font=("Segoe UI", 10), width=14,
                     state="readonly").pack(anchor="w", ipady=4)

        br = tk.Frame(self, bg=COLORS["main_bg"])
        br.pack(fill="x", padx=24, pady=14, side="bottom")
        styled_btn(br, "  Save", self._save,
                   color=COLORS["success"], padx=22, pady=9).pack(side="left")
        styled_btn(br, "Cancel", self.destroy,
                   color=COLORS["danger"], padx=14, pady=9).pack(side="left", padx=10)

    def _load(self):
        conn = get_connection()
        row  = conn.execute("SELECT * FROM staff WHERE id=?", (self.staff_id,)).fetchone()
        conn.close()
        if not row: return
        self._name_e.insert(0,  row["name"])
        self._role_e.insert(0,  row["role"] or "")
        self._hourly_e.insert(0, str(row["hourly_wage"] or row["daily_wage"] or 0))
        self._stdhours_e.delete(0, "end")
        self._stdhours_e.insert(0, str(row["standard_hours"] or 8))
        self._otrate_e.delete(0, "end")
        self._otrate_e.insert(0, str(row["overtime_rate"] or 1.5))
        self._phone_e.insert(0, row["phone"] or "")
        self._addr_e.insert(0,  row["address"] or "")
        if row["join_date"]: self._join_var.set(row["join_date"])
        self._status_var.set(row["status"] or "active")

    def _save(self):
        name   = self._name_e.get().strip()
        role   = self._role_e.get().strip()
        hourly = self._hourly_e.get().strip()
        stdhrs = self._stdhours_e.get().strip()
        otrate = self._otrate_e.get().strip()
        phone  = self._phone_e.get().strip()
        addr   = self._addr_e.get().strip()
        join   = self._join_var.get().strip()
        status = self._status_var.get()

        if not name:
            messagebox.showwarning("Required", "Please enter staff name.", parent=self); return
        if not role:
            messagebox.showwarning("Required", "Please enter a role/position.", parent=self); return
        try:
            hourly_f = float(hourly)
            if hourly_f < 0: raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid", "Enter a valid hourly wage.", parent=self); return
        try:
            stdhrs_f = float(stdhrs)
            if stdhrs_f <= 0: raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid", "Enter valid standard hours (e.g. 8).", parent=self); return
        try:
            otrate_f = float(otrate)
            if otrate_f < 1: raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid", "Overtime multiplier must be >= 1.0.", parent=self); return

        conn = get_connection()
        if self.staff_id:
            conn.execute("""UPDATE staff SET name=?,role=?,hourly_wage=?,standard_hours=?,
                overtime_rate=?,phone=?,address=?,join_date=?,status=? WHERE id=?""",
                (name, role, hourly_f, stdhrs_f, otrate_f,
                 phone, addr, join, status, self.staff_id))
        else:
            conn.execute("""INSERT INTO staff
                (name,role,hourly_wage,standard_hours,overtime_rate,phone,address,join_date,status)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (name, role, hourly_f, stdhrs_f, otrate_f,
                 phone, addr, join, status))
        conn.commit(); conn.close()
        self.on_saved(); self.destroy()


# =============================================================================
#  ATTENDANCE WINDOW  — hourly grid with overtime
# =============================================================================

class AttendanceWindow(tk.Toplevel):
    def __init__(self, parent, staff_id, staff_name):
        super().__init__(parent)
        self.staff_id   = staff_id
        self.staff_name = staff_name
        self.title(f"Attendance — {staff_name}")
        self.geometry("900x640")
        self.configure(bg=COLORS["main_bg"])
        self.grab_set()
        self._day_vars   = {}   # date_str -> {"status": StringVar, "hours": StringVar}
        self._std_hours  = 8.0
        self._hourly_wage= 0.0
        self._ot_rate    = 1.5
        self._build()
        self._load_month()

    def _build(self):
        # Header
        h = tk.Frame(self, bg=COLORS["sidebar_bg"], height=52)
        h.pack(fill="x"); h.pack_propagate(False)
        tk.Label(h, text=f"  Attendance & Hours — {self.staff_name}",
                 bg=COLORS["sidebar_bg"], fg="white",
                 font=("Segoe UI", 13, "bold")).pack(side="left", padx=16, pady=10)

        # Month / Year selector
        ctrl = tk.Frame(self, bg=COLORS["white"],
                        highlightbackground=COLORS["border"], highlightthickness=1)
        ctrl.pack(fill="x")

        months = ["January","February","March","April","May","June",
                  "July","August","September","October","November","December"]
        tk.Label(ctrl, text="Month:", bg=COLORS["white"],
                 fg=COLORS["text_dark"], font=("Segoe UI", 10)
                 ).pack(side="left", padx=(14,4), pady=10)
        self._month_var = tk.StringVar(value=months[datetime.date.today().month - 1])
        ttk.Combobox(ctrl, textvariable=self._month_var, values=months,
                     font=("Segoe UI", 10), width=12, state="readonly"
                     ).pack(side="left", pady=10)

        years = [str(y) for y in range(2020, datetime.date.today().year + 2)]
        tk.Label(ctrl, text="Year:", bg=COLORS["white"],
                 fg=COLORS["text_dark"], font=("Segoe UI", 10)
                 ).pack(side="left", padx=(12,4))
        self._year_var = tk.StringVar(value=str(datetime.date.today().year))
        ttk.Combobox(ctrl, textvariable=self._year_var, values=years,
                     font=("Segoe UI", 10), width=8, state="readonly"
                     ).pack(side="left", pady=10)

        styled_btn(ctrl, "  Load", self._load_month,
                   color=COLORS["accent"], padx=14, pady=5).pack(side="left", padx=10)

        # Wage info strip
        self._wage_lbl = tk.Label(self, text="",
                                  bg=COLORS["sidebar_bg"], fg="white",
                                  font=("Segoe UI", 9))
        self._wage_lbl.pack(fill="x", ipady=4)

        # Summary strip
        self._summary_lbl = tk.Label(self, text="",
                                     bg=COLORS["label_bg"], fg=COLORS["text_dark"],
                                     font=("Segoe UI", 10))
        self._summary_lbl.pack(fill="x", ipady=6)

        # Legend
        leg = tk.Frame(self, bg=COLORS["white"])
        leg.pack(fill="x", padx=16, pady=(6,0))
        for color, label in [
            (COLORS["success"], "Present"),
            (COLORS["danger"],  "Absent"),
            (COLORS["warning"], "Half Day"),
            (COLORS["accent"],  "Overtime (hours > standard)"),
        ]:
            dot = tk.Frame(leg, bg=color, width=12, height=12)
            dot.pack(side="left", padx=(0,4))
            tk.Label(leg, text=label, bg=COLORS["white"],
                     fg=COLORS["text_dark"], font=("Segoe UI", 9)
                     ).pack(side="left", padx=(0,16))

        # Calendar grid (scrollable)
        canvas = tk.Canvas(self, bg=COLORS["main_bg"], highlightthickness=0)
        sb = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True, padx=12, pady=6)

        self._grid_frame = tk.Frame(canvas, bg=COLORS["main_bg"])
        win = canvas.create_window((0,0), window=self._grid_frame, anchor="nw")
        self._grid_frame.bind("<Configure>",
                              lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))

        # Buttons
        br = tk.Frame(self, bg=COLORS["main_bg"])
        br.pack(fill="x", padx=16, pady=(0,12), side="bottom")
        styled_btn(br, "  Save Attendance", self._save_attendance,
                   color=COLORS["success"], padx=22, pady=9).pack(side="left")
        styled_btn(br, "  Recalculate", self._recalculate,
                   color=COLORS["accent"], padx=14, pady=9).pack(side="left", padx=8)
        styled_btn(br, "Close", self.destroy,
                   color=COLORS["danger"], padx=14, pady=9).pack(side="left")

    def _load_month(self):
        months = ["January","February","March","April","May","June",
                  "July","August","September","October","November","December"]
        month_num = months.index(self._month_var.get()) + 1
        year      = int(self._year_var.get())

        conn  = get_connection()
        saved = conn.execute(
            """SELECT date, status, hours_worked, overtime_hours FROM attendance
               WHERE staff_id=? AND strftime('%Y-%m', date)=?""",
            (self.staff_id, f"{year}-{month_num:02d}")).fetchall()
        staff = conn.execute("SELECT * FROM staff WHERE id=?",
                             (self.staff_id,)).fetchone()
        cfg   = {r["key"]: r["value"] for r in
                 conn.execute("SELECT key,value FROM settings").fetchall()}
        conn.close()

        self._curr       = cfg.get("currency_symbol", "Rs.")
        self._std_hours  = float(staff["standard_hours"] or 8)
        self._hourly_wage= float(staff["hourly_wage"] or 0)
        self._ot_rate    = float(staff["overtime_rate"] or 1.5)

        self._wage_lbl.config(
            text=f"   Hourly Wage: {self._curr} {self._hourly_wage:,.0f}   |   "
                 f"Standard Hours/Day: {self._std_hours:.0f} hrs   |   "
                 f"Overtime Rate: {self._ot_rate}x   |   "
                 f"Effective Daily (std): "
                 f"{self._curr} {self._hourly_wage * self._std_hours:,.0f}")

        saved_map = {r["date"]: r for r in saved}
        self._day_vars.clear()

        for w in self._grid_frame.winfo_children():
            w.destroy()

        # Day-of-week headers
        days_header = tk.Frame(self._grid_frame, bg=COLORS["main_bg"])
        days_header.pack(fill="x", pady=(0,4))
        for day_name in ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]:
            tk.Label(days_header, text=day_name,
                     bg=COLORS["sidebar_bg"], fg="white",
                     font=("Segoe UI", 10, "bold"), width=11, anchor="center"
                     ).pack(side="left", padx=2)

        _, days_in_month = calendar.monthrange(year, month_num)
        first_weekday, _ = calendar.monthrange(year, month_num)

        week_frame = tk.Frame(self._grid_frame, bg=COLORS["main_bg"])
        week_frame.pack(fill="x", pady=2)

        for _ in range(first_weekday):
            tk.Frame(week_frame, bg=COLORS["main_bg"], width=86, height=96
                     ).pack(side="left", padx=2)

        col = first_weekday
        for day in range(1, days_in_month + 1):
            date_str = f"{year}-{month_num:02d}-{day:02d}"
            saved_row = saved_map.get(date_str)
            status    = saved_row["status"]       if saved_row else "present"
            hrs_val   = saved_row["hours_worked"] if saved_row else self._std_hours

            status_var = tk.StringVar(value=status)
            hours_var  = tk.StringVar(value=str(hrs_val))
            self._day_vars[date_str] = {"status": status_var, "hours": hours_var}

            has_ot = hrs_val > self._std_hours
            cell_bg = self._cell_color(status, has_ot)

            cell = tk.Frame(week_frame, bg=cell_bg, width=86, height=96,
                            highlightbackground=COLORS["border"], highlightthickness=1)
            cell.pack(side="left", padx=2)
            cell.pack_propagate(False)

            # Date number
            is_today = (date_str == str(datetime.date.today()))
            num_bg = COLORS["sidebar_bg"] if is_today else cell_bg
            num_fg = "white" if is_today else COLORS["text_dark"]
            tk.Label(cell, text=str(day), bg=num_bg, fg=num_fg,
                     font=("Segoe UI", 11, "bold")).pack(pady=(4,1))

            # Hours entry
            hrs_entry = tk.Entry(cell, textvariable=hours_var, width=5,
                                 font=("Segoe UI", 9), justify="center",
                                 bg=COLORS["white"], fg=COLORS["text_dark"],
                                 relief="flat", highlightthickness=1,
                                 highlightbackground=COLORS["border"])
            hrs_entry.pack(pady=(1,2))
            tk.Label(cell, text="hrs", bg=cell_bg, fg=COLORS["text_muted"],
                     font=("Segoe UI", 7)).pack()

            # Status P / A / H buttons
            btns_f = tk.Frame(cell, bg=cell_bg)
            btns_f.pack()

            def make_btn(parent, lbl, val,
                         sv=status_var, hv=hours_var,
                         c=cell, bf=btns_f, he=hrs_entry, ds=date_str):
                def click():
                    sv.set(val)
                    # Auto-fill hours based on status
                    if val == "absent":
                        hv.set("0")
                    elif val == "half-day":
                        hv.set(str(self._std_hours / 2))
                    elif val == "present" and hv.get() == "0":
                        hv.set(str(self._std_hours))
                    self._refresh_cell(c, bf, he, sv, hv)
                    self._recalculate()

                clr = {"P": COLORS["success"],
                       "A": COLORS["danger"],
                       "H": COLORS["warning"]}[lbl]
                return tk.Button(parent, text=lbl, bg=clr, fg="white",
                                 font=("Segoe UI", 8, "bold"), relief="flat",
                                 cursor="hand2", width=2, padx=1, pady=1,
                                 command=click)

            make_btn(btns_f, "P", "present").pack(side="left",  padx=1, pady=1)
            make_btn(btns_f, "A", "absent").pack(side="left",   padx=1, pady=1)
            make_btn(btns_f, "H", "half-day").pack(side="left", padx=1, pady=1)

            # Live recalc when hours change
            hours_var.trace("w", lambda *a, sv=status_var, hv=hours_var,
                            c=cell, bf=btns_f, he=hrs_entry: (
                self._refresh_cell(c, bf, he, sv, hv),
                self._recalculate()
            ))

            col += 1
            if col == 7 and day < days_in_month:
                col = 0
                week_frame = tk.Frame(self._grid_frame, bg=COLORS["main_bg"])
                week_frame.pack(fill="x", pady=2)

        self._recalculate()

    def _cell_color(self, status, has_ot=False):
        if status == "absent":   return COLORS["absent_bg"]
        if status == "half-day": return COLORS["halfday_bg"]
        if has_ot:               return COLORS["overtime_bg"]
        return COLORS["present_bg"]

    def _refresh_cell(self, cell, btns_f, hrs_entry, sv, hv):
        try:   hrs = float(hv.get() or 0)
        except: hrs = 0
        has_ot = hrs > self._std_hours
        new_bg = self._cell_color(sv.get(), has_ot)
        cell.config(bg=new_bg)
        btns_f.config(bg=new_bg)
        hrs_entry.config(highlightbackground=
                         COLORS["accent"] if has_ot else COLORS["border"])
        for w in cell.winfo_children():
            try:
                if w != hrs_entry: w.config(bg=new_bg)
            except: pass

    def _recalculate(self):
        total_regular_hrs = 0.0
        total_ot_hrs      = 0.0
        present_days      = 0
        absent_days       = 0
        halfday_days      = 0

        for date_str, d in self._day_vars.items():
            status = d["status"].get()
            try:   hrs = float(d["hours"].get() or 0)
            except: hrs = 0.0

            if status == "absent":
                absent_days += 1
            elif status == "half-day":
                halfday_days += 1
                regular = min(hrs, self._std_hours / 2)
                ot      = max(0, hrs - self._std_hours / 2)
                total_regular_hrs += regular
                total_ot_hrs      += ot
            else:  # present
                present_days += 1
                regular = min(hrs, self._std_hours)
                ot      = max(0, hrs - self._std_hours)
                total_regular_hrs += regular
                total_ot_hrs      += ot

        regular_pay = total_regular_hrs * self._hourly_wage
        ot_pay      = total_ot_hrs      * self._hourly_wage * self._ot_rate
        total_pay   = regular_pay + ot_pay

        self._summary_lbl.config(
            text=f"   Present: {present_days}   |   Half-Day: {halfday_days}   |"
                 f"   Absent: {absent_days}   |"
                 f"   Regular Hrs: {total_regular_hrs:.1f}   |"
                 f"   Overtime Hrs: {total_ot_hrs:.1f}   |"
                 f"   Regular Pay: {self._curr} {regular_pay:,.0f}   |"
                 f"   OT Pay: {self._curr} {ot_pay:,.0f}   |"
                 f"   TOTAL SALARY: {self._curr} {total_pay:,.0f}")

    def _save_attendance(self):
        conn = get_connection()
        for date_str, d in self._day_vars.items():
            status = d["status"].get()
            try:   hrs = float(d["hours"].get() or 0)
            except: hrs = 0.0
            ot_hrs = max(0, hrs - self._std_hours) if status != "absent" else 0.0
            conn.execute("""INSERT INTO attendance
                (staff_id, date, status, hours_worked, overtime_hours)
                VALUES (?,?,?,?,?)
                ON CONFLICT(staff_id,date) DO UPDATE SET
                    status=excluded.status,
                    hours_worked=excluded.hours_worked,
                    overtime_hours=excluded.overtime_hours""",
                (self.staff_id, date_str, status, hrs, ot_hrs))
        conn.commit(); conn.close()
        messagebox.showinfo("Saved", "Attendance saved successfully!", parent=self)


# =============================================================================
#  STAFF DETAIL PANEL
# =============================================================================

class StaffDetailPanel(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORS["white"], **kwargs)
        self._build_empty()

    def _build_empty(self):
        for w in self.winfo_children(): w.destroy()
        tk.Label(self, text="👤", bg=COLORS["white"],
                 font=("Segoe UI Emoji", 40)).pack(pady=(40,8))
        tk.Label(self, text="Select a staff member\nto view details",
                 bg=COLORS["white"], fg=COLORS["text_muted"],
                 font=("Segoe UI", 11), justify="center").pack()

    def load(self, staff_id, on_edit, on_attendance):
        for w in self.winfo_children(): w.destroy()

        conn = get_connection()
        s    = conn.execute("SELECT * FROM staff WHERE id=?", (staff_id,)).fetchone()

        today      = datetime.date.today()
        month_str  = today.strftime("%Y-%m")
        att        = conn.execute(
            """SELECT status, SUM(hours_worked) as total_hrs,
                      SUM(overtime_hours) as total_ot, COUNT(*) as days
               FROM attendance
               WHERE staff_id=? AND strftime('%Y-%m',date)=?
               GROUP BY status""",
            (staff_id, month_str)).fetchall()

        cfg  = {r["key"]: r["value"] for r in
                conn.execute("SELECT key,value FROM settings").fetchall()}
        conn.close()

        curr      = cfg.get("currency_symbol", "Rs.")
        hourly    = float(s["hourly_wage"] or 0)
        std_hrs   = float(s["standard_hours"] or 8)
        ot_rate   = float(s["overtime_rate"] or 1.5)

        total_regular_hrs = 0.0
        total_ot_hrs      = 0.0
        present_days      = 0

        for r in att:
            if r["status"] != "absent":
                total_regular_hrs += min(float(r["total_hrs"] or 0),
                                         float(r["days"]) * std_hrs)
                total_ot_hrs      += float(r["total_ot"] or 0)
                if r["status"] == "present":
                    present_days += int(r["days"])

        salary = (total_regular_hrs * hourly) + (total_ot_hrs * hourly * ot_rate)

        # Avatar
        av = tk.Frame(self, bg=COLORS["accent"], width=64, height=64)
        av.pack(pady=(20,8)); av.pack_propagate(False)
        initials = "".join(p[0].upper() for p in s["name"].split()[:2])
        tk.Label(av, text=initials, bg=COLORS["accent"], fg="white",
                 font=("Segoe UI", 20, "bold")).place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(self, text=s["name"], bg=COLORS["white"], fg=COLORS["text_dark"],
                 font=("Segoe UI", 14, "bold")).pack()
        tk.Label(self, text=s["role"] or "—", bg=COLORS["white"],
                 fg=COLORS["accent"], font=("Segoe UI", 10)).pack(pady=(0,8))

        sc = COLORS["success"] if s["status"] == "active" else COLORS["danger"]
        tk.Label(self, text=f"  {s['status'].upper()}  ", bg=sc, fg="white",
                 font=("Segoe UI", 9, "bold")).pack(pady=(0,10))

        tk.Frame(self, bg=COLORS["border"], height=1).pack(fill="x", padx=20, pady=4)

        def info_row(icon, label, value):
            r = tk.Frame(self, bg=COLORS["white"]); r.pack(fill="x", padx=14, pady=2)
            tk.Label(r, text=icon, bg=COLORS["white"],
                     font=("Segoe UI Emoji", 10), width=3).pack(side="left")
            tk.Label(r, text=label, bg=COLORS["white"], fg=COLORS["text_muted"],
                     font=("Segoe UI", 9), width=13, anchor="w").pack(side="left")
            tk.Label(r, text=str(value), bg=COLORS["white"], fg=COLORS["text_dark"],
                     font=("Segoe UI", 9)).pack(side="left")

        info_row("💰", "Hourly Wage:",  f"{curr} {hourly:,.0f}")
        info_row("⏱",  "Std Hours:",   f"{std_hrs:.0f} hrs/day")
        info_row("📈", "OT Rate:",      f"{ot_rate}x")
        info_row("📞", "Phone:",        s["phone"] or "—")
        info_row("📅", "Joined:",       s["join_date"] or "—")

        tk.Frame(self, bg=COLORS["border"], height=1).pack(fill="x", padx=20, pady=6)
        tk.Label(self, text="This Month", bg=COLORS["white"],
                 fg=COLORS["text_muted"], font=("Segoe UI", 9, "bold")
                 ).pack(anchor="w", padx=14)

        mf = tk.Frame(self, bg=COLORS["label_bg"])
        mf.pack(fill="x", padx=14, pady=4)
        for lbl, val, clr in [
            ("Reg Hrs",  f"{total_regular_hrs:.1f}",   COLORS["success"]),
            ("OT Hrs",   f"{total_ot_hrs:.1f}",        COLORS["accent"]),
            ("Salary",   f"{curr} {salary:,.0f}",      COLORS["warning"]),
        ]:
            c = tk.Frame(mf, bg=COLORS["label_bg"])
            c.pack(side="left", expand=True, fill="both", padx=4, pady=8)
            tk.Label(c, text=val, bg=COLORS["label_bg"], fg=clr,
                     font=("Segoe UI", 13, "bold")).pack()
            tk.Label(c, text=lbl, bg=COLORS["label_bg"], fg=COLORS["text_muted"],
                     font=("Segoe UI", 8)).pack()

        btns = tk.Frame(self, bg=COLORS["white"])
        btns.pack(fill="x", padx=14, pady=8)
        styled_btn(btns, "  Edit", on_edit,
                   color=COLORS["accent"], padx=12, pady=7).pack(side="left", padx=(0,8))
        styled_btn(btns, "  Attendance", on_attendance,
                   color=COLORS["success"], padx=10, pady=7).pack(side="left")


# =============================================================================
#  MAIN STAFF PAGE
# =============================================================================

class StaffPage(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORS["main_bg"], **kwargs)
        self._selected_id = None
        self._build()
        self._load()

    def _build(self):
        bar = tk.Frame(self, bg=COLORS["white"],
                       highlightbackground=COLORS["border"], highlightthickness=1)
        bar.pack(fill="x")

        styled_btn(bar, "  Add Staff Member", self._add_staff,
                   color=COLORS["success"], padx=18, pady=10).pack(side="left", padx=12, pady=8)

        sf = tk.Frame(bar, bg=COLORS["white"],
                      highlightbackground=COLORS["border"], highlightthickness=1)
        sf.pack(side="left", padx=8, pady=8)
        tk.Label(sf, text="Search:", bg=COLORS["white"],
                 font=("Segoe UI", 10)).pack(side="left", padx=6)
        self._search_var = tk.StringVar()
        self._search_var.trace("w", lambda *a: self._load())
        tk.Entry(sf, textvariable=self._search_var, width=20,
                 font=("Segoe UI", 10), bg=COLORS["white"], fg=COLORS["text_dark"],
                 relief="flat", insertbackground=COLORS["text_dark"]
                 ).pack(side="left", ipady=5, padx=4)

        self._filter_var = tk.StringVar(value="active")
        for val, lbl in [("all","All"),("active","Active"),("inactive","Inactive")]:
            tk.Radiobutton(bar, text=lbl, variable=self._filter_var, value=val,
                           bg=COLORS["white"], fg=COLORS["text_dark"],
                           font=("Segoe UI", 10), activebackground=COLORS["white"],
                           selectcolor=COLORS["white"],
                           command=self._load).pack(side="left", padx=6)

        content = tk.Frame(self, bg=COLORS["main_bg"])
        content.pack(fill="both", expand=True)

        left = tk.Frame(content, bg=COLORS["white"],
                        highlightbackground=COLORS["border"], highlightthickness=1)
        left.pack(side="left", fill="both", expand=True)

        style = ttk.Style()
        style.configure("Treeview",         rowheight=34, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        cols = ("Name","Role","Hourly Wage","Std Hours","OT Rate","Phone","Status")
        self._tree = ttk.Treeview(left, columns=cols, show="headings", selectmode="browse")
        for col, w in zip(cols, [150, 120, 100, 90, 80, 120, 80]):
            self._tree.heading(col, text=col)
            self._tree.column(col, width=w, anchor="w")

        self._tree.tag_configure("active",   background=COLORS["present_bg"])
        self._tree.tag_configure("inactive", background=COLORS["absent_bg"])

        vsb = ttk.Scrollbar(left, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True)
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        self._menu = tk.Menu(self, tearoff=0)
        self._menu.add_command(label="Mark Attendance",   command=self._open_attendance)
        self._menu.add_command(label="Edit Staff Member", command=self._edit_staff)
        self._menu.add_separator()
        self._menu.add_command(label="Set Inactive", command=lambda: self._set_status("inactive"))
        self._menu.add_command(label="Set Active",   command=lambda: self._set_status("active"))
        self._menu.add_separator()
        self._menu.add_command(label="Delete Staff Member", command=self._delete_staff)
        self._tree.bind("<Button-3>", self._show_menu)

        self._detail = StaffDetailPanel(content, width=270)
        self._detail.pack(side="right", fill="y")
        self._detail.pack_propagate(False)

        self._summary_lbl = tk.Label(self, text="",
                                     bg=COLORS["label_bg"], fg=COLORS["text_muted"],
                                     font=("Segoe UI", 10))
        self._summary_lbl.pack(fill="x", side="bottom", ipady=5)

    def _load(self):
        q   = self._search_var.get().strip()
        fv  = self._filter_var.get()
        conn = get_connection()
        cfg  = {r["key"]: r["value"] for r in
                conn.execute("SELECT key,value FROM settings").fetchall()}
        sql  = "SELECT * FROM staff WHERE 1=1"
        params = []
        if fv != "all": sql += " AND status=?"; params.append(fv)
        if q:           sql += " AND name LIKE ?"; params.append(f"%{q}%")
        sql += " ORDER BY name"
        rows  = conn.execute(sql, params).fetchall()
        total = conn.execute(
            "SELECT COUNT(*) FROM staff WHERE status='active'").fetchone()[0]
        conn.close()

        curr = cfg.get("currency_symbol", "Rs.")
        self._tree.delete(*self._tree.get_children())
        for r in rows:
            self._tree.insert("", "end", iid=str(r["id"]),
                              values=(
                                  r["name"],
                                  r["role"] or "—",
                                  f"{curr} {r['hourly_wage']:,.0f}/hr",
                                  f"{r['standard_hours'] or 8:.0f} hrs",
                                  f"{r['overtime_rate'] or 1.5}x",
                                  r["phone"] or "—",
                                  r["status"].upper()
                              ),
                              tags=(r["status"],))
        self._summary_lbl.config(
            text=f"     Active Staff: {total}     |     Showing: {len(rows)} records")

    def _on_select(self, e):
        sel = self._tree.focus()
        if sel:
            self._selected_id = int(sel)
            self._detail.load(
                self._selected_id,
                on_edit=self._edit_staff,
                on_attendance=self._open_attendance)

    def _sel_id(self):
        s = self._tree.focus(); return int(s) if s else None

    def _show_menu(self, e):
        r = self._tree.identify_row(e.y)
        if r:
            self._tree.focus(r); self._tree.selection_set(r)
            self._menu.post(e.x_root, e.y_root)

    def _add_staff(self):
        StaffForm(self, on_saved=self._load)

    def _edit_staff(self):
        i = self._sel_id()
        if i:
            StaffForm(self, on_saved=lambda: [
                self._load(),
                self._detail.load(i, on_edit=self._edit_staff,
                                  on_attendance=self._open_attendance)
            ], staff_id=i)

    def _open_attendance(self):
        i = self._sel_id()
        if not i: return
        conn = get_connection()
        name = conn.execute("SELECT name FROM staff WHERE id=?",
                            (i,)).fetchone()["name"]
        conn.close()
        AttendanceWindow(self, i, name)

    def _set_status(self, status):
        i = self._sel_id()
        if not i: return
        conn = get_connection()
        conn.execute("UPDATE staff SET status=? WHERE id=?", (status, i))
        conn.commit(); conn.close()
        self._load()

    def _delete_staff(self):
        i = self._sel_id()
        if not i: return
        if messagebox.askyesno("Delete",
                "Delete this staff member and all attendance records?\n"
                "This cannot be undone.", parent=self):
            conn = get_connection()
            conn.execute("DELETE FROM staff WHERE id=?", (i,))
            conn.commit(); conn.close()
            self._detail._build_empty()
            self._load()

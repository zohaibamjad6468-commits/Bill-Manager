import tkinter as tk
from tkinter import messagebox, ttk
import sys, os, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.db_connection import get_connection

COLORS = {
    "main_bg":    "#F4F6F8",
    "white":      "#FFFFFF",
    "accent":     "#2980B9",
    "text_dark":  "#2C3E50",
    "text_muted": "#7F8C8D",
    "border":     "#DDE1E7",
    "success":    "#27AE60",
    "danger":     "#E74C3C",
    "warning":    "#E67E22",
    "input_bg":   "#FDFDFD",
    "label_bg":   "#F0F3F4",
    "row_alt":    "#F8FAFB",
    "income_bg":  "#EAFAF1",
    "expense_bg": "#FDEDEC",
}

EXPENSE_CATEGORIES = [
    "Rent", "Salaries", "Utilities", "Raw Materials", "Transport",
    "Repairs & Maintenance", "Office Supplies", "Marketing", "Tax",
    "Miscellaneous"
]

def styled_btn(parent, text, command, color=None, fg="white", padx=14, pady=6):
    color = color or COLORS["accent"]
    return tk.Button(parent, text=text, command=command,
                     bg=color, fg=fg, font=("Segoe UI", 10, "bold"),
                     relief="flat", cursor="hand2", padx=padx, pady=pady,
                     activebackground=color, activeforeground=fg)

def styled_entry(parent, width=22):
    return tk.Entry(parent, width=width, font=("Segoe UI", 10),
                    bg=COLORS["input_bg"], fg=COLORS["text_dark"],
                    relief="flat", highlightthickness=1,
                    highlightbackground=COLORS["border"],
                    highlightcolor=COLORS["accent"],
                    insertbackground=COLORS["text_dark"])


# ─────────────────────────────────────────────────────────────────────────────
#  ADD / EDIT EXPENSE WINDOW
# ─────────────────────────────────────────────────────────────────────────────

class ExpenseForm(tk.Toplevel):
    def __init__(self, parent, on_saved, expense_id=None):
        super().__init__(parent)
        self.on_saved   = on_saved
        self.expense_id = expense_id
        self.title("Edit Expense" if expense_id else "Add Expense")
        self.geometry("420x400")
        self.resizable(False, False)
        self.configure(bg=COLORS["main_bg"])
        self.grab_set()
        self._build()
        if expense_id:
            self._load()

    def _build(self):
        # Header
        h = tk.Frame(self, bg=COLORS["warning"], height=46)
        h.pack(fill="x"); h.pack_propagate(False)
        title = "Edit Expense" if self.expense_id else "  Add New Expense"
        tk.Label(h, text=title, bg=COLORS["warning"], fg="white",
                 font=("Segoe UI", 12, "bold")).pack(side="left", padx=14, pady=10)

        f = tk.Frame(self, bg=COLORS["main_bg"])
        f.pack(fill="both", expand=True, padx=20, pady=14)

        # Date
        tk.Label(f, text="Date *", bg=COLORS["main_bg"], fg=COLORS["text_dark"],
                 font=("Segoe UI", 10)).pack(anchor="w")
        self._date_var = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        tk.Entry(f, textvariable=self._date_var, width=20,
                 font=("Segoe UI", 10), bg=COLORS["input_bg"],
                 fg=COLORS["text_dark"], relief="flat",
                 highlightthickness=1, highlightbackground=COLORS["border"]
                 ).pack(anchor="w", ipady=5, pady=(2, 10))

        # Category
        tk.Label(f, text="Category *", bg=COLORS["main_bg"], fg=COLORS["text_dark"],
                 font=("Segoe UI", 10)).pack(anchor="w")
        self._cat_var = tk.StringVar(value=EXPENSE_CATEGORIES[0])
        ttk.Combobox(f, textvariable=self._cat_var, values=EXPENSE_CATEGORIES,
                     font=("Segoe UI", 10), width=28, state="readonly"
                     ).pack(anchor="w", ipady=4, pady=(2, 10))

        # Amount
        tk.Label(f, text="Amount *", bg=COLORS["main_bg"], fg=COLORS["text_dark"],
                 font=("Segoe UI", 10)).pack(anchor="w")
        self._amount_e = styled_entry(f, width=20)
        self._amount_e.pack(anchor="w", ipady=5, pady=(2, 10))

        # Description
        tk.Label(f, text="Description", bg=COLORS["main_bg"], fg=COLORS["text_dark"],
                 font=("Segoe UI", 10)).pack(anchor="w")
        self._desc_e = tk.Text(f, height=3, width=38, font=("Segoe UI", 10),
                               bg=COLORS["input_bg"], fg=COLORS["text_dark"],
                               relief="flat", highlightthickness=1,
                               highlightbackground=COLORS["border"], wrap="word")
        self._desc_e.pack(anchor="w", pady=(2, 0))

        # Buttons pinned to bottom
        br = tk.Frame(self, bg=COLORS["main_bg"])
        br.pack(fill="x", padx=20, pady=12, side="bottom")
        styled_btn(br, "  Save Expense", self._save,
                   color=COLORS["warning"], padx=18, pady=9).pack(side="left")
        styled_btn(br, "Cancel", self.destroy,
                   color=COLORS["danger"], padx=14, pady=9).pack(side="left", padx=10)

    def _load(self):
        conn = get_connection()
        row = conn.execute("SELECT * FROM expenses WHERE id=?", (self.expense_id,)).fetchone()
        conn.close()
        if not row: return
        self._date_var.set(row["date"])
        self._cat_var.set(row["category"])
        self._amount_e.delete(0, "end"); self._amount_e.insert(0, str(row["amount"]))
        if row["description"]: self._desc_e.insert("1.0", row["description"])

    def _save(self):
        date   = self._date_var.get().strip()
        cat    = self._cat_var.get().strip()
        desc   = self._desc_e.get("1.0", "end").strip()
        amount_str = self._amount_e.get().strip()

        if not date:
            messagebox.showwarning("Required", "Please enter a date.", parent=self); return
        if not amount_str:
            messagebox.showwarning("Required", "Please enter an amount.", parent=self); return
        try:
            amount = float(amount_str)
            if amount <= 0: raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid", "Enter a valid positive amount.", parent=self); return

        conn = get_connection()
        if self.expense_id:
            conn.execute("UPDATE expenses SET date=?,category=?,description=?,amount=? WHERE id=?",
                         (date, cat, desc, amount, self.expense_id))
        else:
            conn.execute("INSERT INTO expenses (date,category,description,amount) VALUES (?,?,?,?)",
                         (date, cat, desc, amount))
        conn.commit(); conn.close()
        self.on_saved(); self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
#  CASH FLOW PAGE
# ─────────────────────────────────────────────────────────────────────────────

class CashFlowPage(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORS["main_bg"], **kwargs)
        self._build()
        self._load()

    def _get_cfg(self):
        conn = get_connection()
        cfg = {r["key"]: r["value"] for r in conn.execute("SELECT key,value FROM settings").fetchall()}
        conn.close()
        return cfg

    # ── Build full UI ─────────────────────────────────────────────────────────
    def _build(self):
        # ── Top bar ───────────────────────────────────────────────────────────
        bar = tk.Frame(self, bg=COLORS["white"],
                       highlightbackground=COLORS["border"], highlightthickness=1)
        bar.pack(fill="x")

        styled_btn(bar, "  Add Expense", self._add_expense,
                   color=COLORS["warning"], padx=18, pady=10).pack(side="left", padx=12, pady=8)

        # Month / Year selector
        tk.Label(bar, text="Month:", bg=COLORS["white"], fg=COLORS["text_dark"],
                 font=("Segoe UI", 10)).pack(side="left", padx=(12, 4))

        months = ["January","February","March","April","May","June",
                  "July","August","September","October","November","December"]
        self._month_var = tk.StringVar(value=months[datetime.date.today().month - 1])
        ttk.Combobox(bar, textvariable=self._month_var, values=months,
                     font=("Segoe UI", 10), width=12, state="readonly"
                     ).pack(side="left", pady=8)

        tk.Label(bar, text="Year:", bg=COLORS["white"], fg=COLORS["text_dark"],
                 font=("Segoe UI", 10)).pack(side="left", padx=(10, 4))
        years = [str(y) for y in range(2020, datetime.date.today().year + 3)]
        self._year_var = tk.StringVar(value=str(datetime.date.today().year))
        ttk.Combobox(bar, textvariable=self._year_var, values=years,
                     font=("Segoe UI", 10), width=8, state="readonly"
                     ).pack(side="left", pady=8)

        styled_btn(bar, "  View", self._load,
                   color=COLORS["accent"], padx=14, pady=6).pack(side="left", padx=8)

        # ── Summary cards ─────────────────────────────────────────────────────
        self._cards_frame = tk.Frame(self, bg=COLORS["main_bg"])
        self._cards_frame.pack(fill="x", padx=16, pady=(12, 4))

        self._card_labels = {}
        for key, icon, label, color, bg in [
            ("income",  "", "Total Income",   COLORS["success"], "#EAFAF1"),
            ("expense", "", "Total Expenses", COLORS["danger"],  "#FDEDEC"),
            ("profit",  "", "Net Profit",     COLORS["accent"],  "#EBF5FB"),
            ("invoices","", "Invoices Raised", "#8E44AD",        "#F5EEF8"),
        ]:
            card = tk.Frame(self._cards_frame, bg=bg,
                            highlightbackground=color, highlightthickness=1)
            card.pack(side="left", fill="both", expand=True, padx=(0, 10))
            tk.Label(card, text=icon, bg=bg,
                     font=("Segoe UI Emoji", 26)).pack(anchor="w", padx=14, pady=(12, 2))
            lbl = tk.Label(card, text="Rs. 0", bg=bg, fg=color,
                           font=("Segoe UI", 20, "bold"))
            lbl.pack(anchor="w", padx=14)
            tk.Label(card, text=label, bg=bg, fg=COLORS["text_muted"],
                     font=("Segoe UI", 10)).pack(anchor="w", padx=14, pady=(0, 12))
            self._card_labels[key] = lbl

        # ── Main content: expenses table + breakdown side by side ─────────────
        content = tk.Frame(self, bg=COLORS["main_bg"])
        content.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        # LEFT: Expenses table
        left = tk.Frame(content, bg=COLORS["white"],
                        highlightbackground=COLORS["border"], highlightthickness=1)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Table header
        th = tk.Frame(left, bg=COLORS["label_bg"])
        th.pack(fill="x")
        tk.Label(th, text="  Monthly Expenses", bg=COLORS["label_bg"],
                 fg=COLORS["text_dark"], font=("Segoe UI", 11, "bold")
                 ).pack(side="left", padx=10, pady=8)
        self._exp_count_lbl = tk.Label(th, text="", bg=COLORS["label_bg"],
                                       fg=COLORS["text_muted"], font=("Segoe UI", 9))
        self._exp_count_lbl.pack(side="left")

        # Treeview
        style = ttk.Style()
        style.configure("Treeview",         rowheight=30, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        cols = ("Date", "Category", "Description", "Amount")
        self._tree = ttk.Treeview(left, columns=cols, show="headings", selectmode="browse")
        for col, w in zip(cols, [90, 130, 200, 100]):
            self._tree.heading(col, text=col)
            self._tree.column(col, width=w, anchor="w")

        vsb = ttk.Scrollbar(left, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True)

        # Right-click menu
        self._menu = tk.Menu(self, tearoff=0)
        self._menu.add_command(label="Edit Expense",   command=self._edit_expense)
        self._menu.add_command(label="Delete Expense", command=self._delete_expense)
        self._tree.bind("<Button-3>", self._show_menu)
        self._tree.bind("<Double-1>", lambda e: self._edit_expense())

        # RIGHT: Breakdown panel
        right = tk.Frame(content, bg=COLORS["white"], width=240,
                         highlightbackground=COLORS["border"], highlightthickness=1)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        tk.Label(right, text="  Category Breakdown", bg=COLORS["label_bg"],
                 fg=COLORS["text_dark"], font=("Segoe UI", 11, "bold")
                 ).pack(fill="x", padx=0, pady=0, ipady=8)

        self._breakdown_frame = tk.Frame(right, bg=COLORS["white"])
        self._breakdown_frame.pack(fill="both", expand=True, padx=10, pady=8)

        # Income breakdown at bottom of right panel
        tk.Frame(right, bg=COLORS["border"], height=1).pack(fill="x", padx=10)
        self._income_detail = tk.Label(right, text="", bg=COLORS["white"],
                                       fg=COLORS["text_muted"], font=("Segoe UI", 9),
                                       justify="left", wraplength=200)
        self._income_detail.pack(anchor="w", padx=12, pady=8)

    # ── Load data ─────────────────────────────────────────────────────────────
    def _load(self):
        months = ["January","February","March","April","May","June",
                  "July","August","September","October","November","December"]
        month_num = months.index(self._month_var.get()) + 1
        year      = int(self._year_var.get())
        month_str = f"{year}-{month_num:02d}"

        cfg  = self._get_cfg()
        curr = cfg.get("currency_symbol", "Rs.")

        conn = get_connection()

        # Expenses for this month
        expenses = conn.execute(
            "SELECT * FROM expenses WHERE strftime('%Y-%m', date)=? ORDER BY date DESC",
            (month_str,)).fetchall()

        # Income from paid/partial invoices this month
        income_rows = conn.execute(
            """SELECT SUM(paid_amount) as total, COUNT(*) as count
               FROM invoices
               WHERE strftime('%Y-%m', date)=? AND status IN ('paid','partial')""",
            (month_str,)).fetchone()

        # All invoices raised this month
        inv_count = conn.execute(
            "SELECT COUNT(*) FROM invoices WHERE strftime('%Y-%m', date)=?",
            (month_str,)).fetchone()[0]

        conn.close()

        total_expense = sum(r["amount"] for r in expenses)
        total_income  = income_rows["total"] or 0
        net_profit    = total_income - total_expense

        # Update summary cards
        profit_color = COLORS["success"] if net_profit >= 0 else COLORS["danger"]
        self._card_labels["income"].config( text=f"{curr} {total_income:,.0f}")
        self._card_labels["expense"].config(text=f"{curr} {total_expense:,.0f}")
        self._card_labels["profit"].config( text=f"{curr} {net_profit:,.0f}", fg=profit_color)
        self._card_labels["invoices"].config(text=str(inv_count))

        # Populate expense table
        self._tree.delete(*self._tree.get_children())
        for r in expenses:
            self._tree.insert("", "end", iid=str(r["id"]),
                              values=(r["date"], r["category"],
                                      r["description"] or "—",
                                      f"{curr} {r['amount']:,.2f}"))

        self._exp_count_lbl.config(text=f"({len(expenses)} entries)")

        # Category breakdown
        for w in self._breakdown_frame.winfo_children():
            w.destroy()

        cat_totals = {}
        for r in expenses:
            cat_totals[r["category"]] = cat_totals.get(r["category"], 0) + r["amount"]

        if cat_totals:
            sorted_cats = sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)
            for cat, amt in sorted_cats:
                pct = (amt / total_expense * 100) if total_expense > 0 else 0
                row = tk.Frame(self._breakdown_frame, bg=COLORS["white"])
                row.pack(fill="x", pady=3)

                tk.Label(row, text=cat, bg=COLORS["white"], fg=COLORS["text_dark"],
                         font=("Segoe UI", 9), width=16, anchor="w").pack(side="left")
                tk.Label(row, text=f"{curr} {amt:,.0f}", bg=COLORS["white"],
                         fg=COLORS["danger"], font=("Segoe UI", 9, "bold"),
                         anchor="e").pack(side="right")

                # Progress bar
                bar_bg = tk.Frame(self._breakdown_frame, bg=COLORS["border"], height=5)
                bar_bg.pack(fill="x", pady=(0, 2))
                bar_fill = tk.Frame(bar_bg, bg=COLORS["danger"], height=5)
                bar_fill.place(relwidth=pct / 100, relheight=1)
        else:
            tk.Label(self._breakdown_frame, text="No expenses\nfor this month",
                     bg=COLORS["white"], fg=COLORS["text_muted"],
                     font=("Segoe UI", 10), justify="center").pack(pady=20)

        # Income detail
        inv_total = conn if False else None
        self._income_detail.config(
            text=f"Income Source:\n"
                 f"  Invoices collected: {income_rows['count'] or 0}\n"
                 f"  Total received: {curr} {total_income:,.0f}")

    # ── Actions ───────────────────────────────────────────────────────────────
    def _add_expense(self):
        ExpenseForm(self, on_saved=self._load)

    def _sel_id(self):
        s = self._tree.focus(); return int(s) if s else None

    def _show_menu(self, e):
        r = self._tree.identify_row(e.y)
        if r:
            self._tree.focus(r); self._tree.selection_set(r)
            self._menu.post(e.x_root, e.y_root)

    def _edit_expense(self):
        i = self._sel_id()
        if i: ExpenseForm(self, on_saved=self._load, expense_id=i)

    def _delete_expense(self):
        i = self._sel_id()
        if not i: return
        if messagebox.askyesno("Delete", "Delete this expense entry?", parent=self):
            conn = get_connection()
            conn.execute("DELETE FROM expenses WHERE id=?", (i,))
            conn.commit(); conn.close()
            self._load()
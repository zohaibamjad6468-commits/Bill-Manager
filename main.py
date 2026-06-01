import sys, os, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk
from database.db_setup import setup_database
from modules.settings import SettingsPage
from modules.invoices import InvoicesPage
from modules.cashflow import CashFlowPage
from modules.staff import StaffPage
from modules.reports import ReportsPage

COLORS = {
    "sidebar_bg":     "#1E2A3A",
    "sidebar_hover":  "#2C3E55",
    "sidebar_active": "#2980B9",
    "sidebar_text":   "#ECF0F1",
    "sidebar_muted":  "#95A5A6",
    "main_bg":        "#F4F6F8",
    "white":          "#FFFFFF",
    "header_text":    "#2C3E50",
    "accent":         "#2980B9",
    "accent_dk":      "#2471A3",
    "text_dark":      "#2C3E50",
    "text_muted":     "#7F8C8D",
    "border":         "#DDE1E7",
    "success":        "#27AE60",
    "warning":        "#F39C12",
    "danger":         "#E74C3C",
    "label_bg":       "#F0F3F4",
    "row_alt":        "#F8FAFB",
    "input_bg":       "#FDFDFD",
}


class SidebarButton(tk.Frame):
    def __init__(self, parent, icon, label, command, **kwargs):
        super().__init__(parent, bg=COLORS["sidebar_bg"], cursor="hand2", **kwargs)
        self.command = command
        self.active = False
        self.icon_lbl = tk.Label(self, text=icon, bg=COLORS["sidebar_bg"],
                                 fg=COLORS["sidebar_text"],
                                 font=("Segoe UI Emoji", 15), width=3)
        self.icon_lbl.pack(side="left", padx=(12,4), pady=12)
        self.text_lbl = tk.Label(self, text=label, bg=COLORS["sidebar_bg"],
                                 fg=COLORS["sidebar_text"],
                                 font=("Segoe UI", 11), anchor="w")
        self.text_lbl.pack(side="left", fill="x", expand=True, pady=12)
        for w in (self, self.icon_lbl, self.text_lbl):
            w.bind("<Enter>",    self._enter)
            w.bind("<Leave>",    self._leave)
            w.bind("<Button-1>", self._click)

    def _enter(self, e):
        if not self.active: self._color(COLORS["sidebar_hover"])
    def _leave(self, e):
        if not self.active: self._color(COLORS["sidebar_bg"])
    def _click(self, e): self.command()
    def set_active(self, state):
        self.active = state
        self._color(COLORS["sidebar_active"] if state else COLORS["sidebar_bg"])
    def _color(self, c):
        self.config(bg=c); self.icon_lbl.config(bg=c); self.text_lbl.config(bg=c)


class PlaceholderPage(tk.Frame):
    def __init__(self, parent, title, desc, icon, **kwargs):
        super().__init__(parent, bg=COLORS["main_bg"], **kwargs)
        c = tk.Frame(self, bg=COLORS["main_bg"])
        c.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(c, text=icon, bg=COLORS["main_bg"],
                 font=("Segoe UI Emoji", 52)).pack(pady=(0,16))
        tk.Label(c, text=title, bg=COLORS["main_bg"],
                 fg=COLORS["text_dark"], font=("Segoe UI", 22, "bold")).pack()
        tk.Label(c, text=desc, bg=COLORS["main_bg"],
                 fg=COLORS["text_muted"], font=("Segoe UI", 12),
                 wraplength=400, justify="center").pack(pady=(8,0))
        tk.Label(c, text="🔧  Module coming soon",
                 bg=COLORS["main_bg"], fg=COLORS["accent"],
                 font=("Segoe UI", 10)).pack(pady=(20,0))


class DashboardPage(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORS["main_bg"], **kwargs)
        self._card_labels = {}
        self._build()
        self._refresh()

    def _build(self):
        # Welcome banner
        banner = tk.Frame(self, bg=COLORS["accent"], height=90)
        banner.pack(fill="x", padx=24, pady=(24,0))
        banner.pack_propagate(False)
        tk.Label(banner, text="👋  S&H Manufacturing Sulzer Loom Parts",
                 bg=COLORS["accent"], fg="white",
                 font=("Segoe UI", 18, "bold")).pack(side="left", padx=24, pady=20)
        tk.Label(banner, text="We Provide the Best Quality at S&H",
                 bg=COLORS["accent"], fg="#D6EAF8",
                 font=("Segoe UI", 11)).pack(side="left")

        # Refresh button on banner
        tk.Button(banner, text="↻  Refresh", command=self._refresh,
                  bg=COLORS["accent_dk"] if "accent_dk" in COLORS else "#2471A3",
                  fg="white", font=("Segoe UI", 10), relief="flat",
                  cursor="hand2", padx=12, pady=6
                  ).pack(side="right", padx=20)

        # ── Stat cards ────────────────────────────────────────────────────────
        cards_frame = tk.Frame(self, bg=COLORS["main_bg"])
        cards_frame.pack(fill="x", padx=24, pady=20)

        card_defs = [
            ("total_inv",    "🧾", "Total Invoices",    "#2980B9", "#EBF5FB"),
            ("paid_inv",     "✅", "Paid Invoices",      "#27AE60", "#EAFAF1"),
            ("unpaid_inv",   "⏳", "Unpaid Invoices",    "#F39C12", "#FEF9E7"),
            ("active_staff", "👷", "Active Staff",       "#8E44AD", "#F5EEF8"),
        ]

        for key, icon, label, color, bg in card_defs:
            card = tk.Frame(cards_frame, bg=bg,
                            highlightbackground=color, highlightthickness=1)
            card.pack(side="left", fill="both", expand=True, padx=(0,12))
            tk.Label(card, text=icon, bg=bg,
                     font=("Segoe UI Emoji", 28)).pack(anchor="w", padx=16, pady=(16,4))
            val_lbl = tk.Label(card, text="—", bg=bg, fg=color,
                               font=("Segoe UI", 26, "bold"))
            val_lbl.pack(anchor="w", padx=16)
            tk.Label(card, text=label, bg=bg, fg=COLORS["text_muted"],
                     font=("Segoe UI", 10)).pack(anchor="w", padx=16, pady=(0,4))
            # Sub-label for extra info
            sub_lbl = tk.Label(card, text="", bg=bg, fg=color,
                               font=("Segoe UI", 9))
            sub_lbl.pack(anchor="w", padx=16, pady=(0,12))
            self._card_labels[key] = (val_lbl, sub_lbl)

        # ── This month summary strip ──────────────────────────────────────────
        self._month_strip = tk.Label(self, text="",
                                     bg=COLORS["label_bg"], fg=COLORS["text_muted"],
                                     font=("Segoe UI", 10))
        self._month_strip.pack(fill="x", ipady=7, padx=0)

        # ── Recent invoices ───────────────────────────────────────────────────
        recent_card = tk.Frame(self, bg=COLORS["white"],
                               highlightbackground=COLORS["border"], highlightthickness=1)
        recent_card.pack(fill="x", padx=24, pady=(0,12))

        hdr = tk.Frame(recent_card, bg=COLORS["label_bg"])
        hdr.pack(fill="x")
        tk.Label(hdr, text="  🧾  Recent Invoices", bg=COLORS["label_bg"],
                 fg=COLORS["text_dark"], font=("Segoe UI", 11, "bold")
                 ).pack(side="left", padx=8, pady=8)

        cols = ("Invoice #", "Customer", "Date", "Amount", "Status")
        style = ttk.Style()
        style.configure("Dash.Treeview", rowheight=28, font=("Segoe UI", 10))
        style.configure("Dash.Treeview.Heading", font=("Segoe UI", 10, "bold"))
        self._recent_tree = ttk.Treeview(recent_card, columns=cols,
                                          show="headings", height=5,
                                          style="Dash.Treeview")
        for col, w in zip(cols, [120, 200, 100, 120, 90]):
            self._recent_tree.heading(col, text=col)
            self._recent_tree.column(col, width=w, anchor="w")
        self._recent_tree.tag_configure("paid",    background="#EAFAF1")
        self._recent_tree.tag_configure("unpaid",  background="#FEF9E7")
        self._recent_tree.tag_configure("partial", background="#EBF5FB")
        self._recent_tree.pack(fill="x", padx=0)

        # ── Quick start guide ────────────────────────────────────────────────
        guide = tk.Frame(self, bg=COLORS["white"],
                         highlightbackground=COLORS["border"], highlightthickness=1)
        guide.pack(fill="both", expand=True, padx=24, pady=(0,24))
        tk.Label(guide, text="🚀  Quick Start Guide", bg=COLORS["white"],
                 fg=COLORS["text_dark"], font=("Segoe UI", 13, "bold")
                 ).pack(anchor="w", padx=20, pady=(14,4))
        tk.Frame(guide, bg=COLORS["border"], height=1).pack(fill="x", padx=20)

        for num, text in [
            ("1", "Go to Settings and enter your Company Name, Address & Phone"),
            ("2", "Add your Customers before creating your first Invoice"),
            ("3", "Create Invoices and track payment status"),
            ("4", "Add Staff members and mark daily Attendance"),
            ("5", "Log monthly Expenses in Cash Flow"),
            ("6", "Generate monthly PDF Reports"),
        ]:
            row = tk.Frame(guide, bg=COLORS["white"])
            row.pack(fill="x", padx=20, pady=5)
            tk.Label(row, text=num, bg=COLORS["accent"], fg="white",
                     font=("Segoe UI", 10, "bold"), width=2
                     ).pack(side="left", padx=(0,12))
            tk.Label(row, text=text, bg=COLORS["white"],
                     fg=COLORS["text_dark"],
                     font=("Segoe UI", 11)).pack(side="left")

    def _refresh(self):
        try:
            from database.db_connection import get_connection
            conn = get_connection()

            # Card values
            total_inv    = conn.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
            paid_inv     = conn.execute("SELECT COUNT(*) FROM invoices WHERE status='paid'").fetchone()[0]
            unpaid_inv   = conn.execute("SELECT COUNT(*) FROM invoices WHERE status='unpaid'").fetchone()[0]
            partial_inv  = conn.execute("SELECT COUNT(*) FROM invoices WHERE status='partial'").fetchone()[0]
            active_staff = conn.execute("SELECT COUNT(*) FROM staff WHERE status='active'").fetchone()[0]

            # Currency
            cfg  = {r["key"]:r["value"] for r in conn.execute("SELECT key,value FROM settings").fetchall()}
            curr = cfg.get("currency_symbol","Rs.")

            # This month figures
            month_str    = datetime.date.today().strftime("%Y-%m")
            month_income = conn.execute(
                "SELECT COALESCE(SUM(paid_amount),0) FROM invoices WHERE strftime('%Y-%m',date)=?",
                (month_str,)).fetchone()[0]
            month_exp    = conn.execute(
                "SELECT COALESCE(SUM(amount),0) FROM expenses WHERE strftime('%Y-%m',date)=?",
                (month_str,)).fetchone()[0]
            total_outstanding = conn.execute(
                "SELECT COALESCE(SUM(total_amount-paid_amount),0) FROM invoices WHERE status!='paid'"
            ).fetchone()[0]

            # Recent 5 invoices
            recent = conn.execute("""
                SELECT i.invoice_number, c.name, i.date, i.total_amount, i.status
                FROM invoices i LEFT JOIN customers c ON i.customer_id=c.id
                ORDER BY i.id DESC LIMIT 5""").fetchall()
            conn.close()

            # Update card values
            updates = {
                "total_inv":    (str(total_inv),    f"Outstanding: {curr} {total_outstanding:,.0f}"),
                "paid_inv":     (str(paid_inv),      "Fully paid"),
                "unpaid_inv":   (str(unpaid_inv),    f"Partial: {partial_inv}"),
                "active_staff": (str(active_staff),  "Currently working"),
            }
            for key, (val, sub) in updates.items():
                self._card_labels[key][0].config(text=val)
                self._card_labels[key][1].config(text=sub)

            # Month strip
            net = month_income - month_exp
            net_color = COLORS["success"] if net >= 0 else COLORS["danger"]
            self._month_strip.config(
                text=f"     This Month:     "
                     f"Income: {curr} {month_income:,.0f}     |     "
                     f"Expenses: {curr} {month_exp:,.0f}     |     "
                     f"Net: {curr} {net:,.0f}")

            # Recent invoices table
            self._recent_tree.delete(*self._recent_tree.get_children())
            for r in recent:
                self._recent_tree.insert("","end",
                    values=(r["invoice_number"], r["name"] or "—",
                            r["date"],
                            f"{curr} {r['total_amount']:,.0f}",
                            r["status"].upper()),
                    tags=(r["status"],))

        except Exception:
            pass  # DB not ready yet on first launch

        # Auto-refresh every 30 seconds
        self.after(30000, self._refresh)


class BillingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BillManager — Business Billing & Management")
        self.geometry("1200x720")
        self.minsize(900, 600)
        self.configure(bg=COLORS["sidebar_bg"])
        setup_database()
        self._active_btn = None
        self._pages = {}
        self._build_layout()
        self._show_page("Dashboard")

    def _build_layout(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=COLORS["sidebar_bg"], width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        logo = tk.Frame(self.sidebar, bg=COLORS["sidebar_bg"], height=72)
        logo.pack(fill="x")
        logo.pack_propagate(False)
        tk.Label(logo, text="💼  BillManager", bg=COLORS["sidebar_bg"],
                 fg="white", font=("Segoe UI",14,"bold")).pack(padx=16, pady=20, anchor="w")
        tk.Frame(self.sidebar, bg=COLORS["sidebar_hover"], height=1).pack(fill="x")

        def add_section(title):
            tk.Label(self.sidebar, text=title, bg=COLORS["sidebar_bg"],
                     fg=COLORS["sidebar_muted"],
                     font=("Segoe UI",8,"bold")).pack(anchor="w", padx=16, pady=(14,2))

        def add_btn(icon, label, page):
            btn = SidebarButton(self.sidebar, icon, label,
                                command=lambda p=page: self._show_page(p))
            btn.pack(fill="x")
            self._pages[page] = {"button": btn, "frame": None}

        add_section("MAIN")
        add_btn("🏠","Dashboard","Dashboard")
        add_btn("🧾","Invoices","Invoices")
        add_btn("💰","Cash Flow","Cash Flow")

        tk.Frame(self.sidebar, bg=COLORS["sidebar_hover"], height=1).pack(fill="x", pady=8)
        add_section("MANAGEMENT")
        add_btn("👷","Staff","Staff")
        add_btn("📋","Attendance","Attendance")
        add_btn("📊","Reports","Reports")

        tk.Frame(self.sidebar, bg=COLORS["sidebar_hover"], height=1).pack(fill="x", pady=8)
        add_section("SYSTEM")
        add_btn("⚙️","Settings","Settings")

        tk.Label(self.sidebar, text="v1.0.0", bg=COLORS["sidebar_bg"],
                 fg=COLORS["sidebar_muted"], font=("Segoe UI",9)
                 ).pack(side="bottom", pady=12)

        # Content area
        right = tk.Frame(self, bg=COLORS["main_bg"])
        right.pack(side="left", fill="both", expand=True)

        self.header = tk.Frame(right, bg=COLORS["white"], height=56,
                               highlightbackground=COLORS["border"], highlightthickness=1)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)
        self.header_title = tk.Label(self.header, text="Dashboard",
                                     bg=COLORS["white"], fg=COLORS["header_text"],
                                     font=("Segoe UI",15,"bold"))
        self.header_title.pack(side="left", padx=24, pady=14)

        self.content = tk.Frame(right, bg=COLORS["main_bg"])
        self.content.pack(fill="both", expand=True)

        # Build all pages
        page_builders = {
            "Dashboard":  lambda: DashboardPage(self.content),
            "Invoices":   lambda: InvoicesPage(self.content),
            "Cash Flow":  lambda: CashFlowPage(self.content),
            "Staff":      lambda: StaffPage(self.content),
            "Attendance": lambda: StaffPage(self.content),
            "Reports":    lambda: ReportsPage(self.content),
            "Settings":   lambda: SettingsPage(self.content),
        }
        for name, builder in page_builders.items():
            frame = builder()
            frame.place(relwidth=1, relheight=1)
            self._pages[name]["frame"] = frame

    def _show_page(self, name):
        if self._active_btn:
            self._active_btn.set_active(False)
        self._pages[name]["button"].set_active(True)
        self._active_btn = self._pages[name]["button"]
        self._pages[name]["frame"].lift()
        self.header_title.config(text=name)


if __name__ == "__main__":
    app = BillingApp()
    app.mainloop()
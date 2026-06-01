import tkinter as tk
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.db_connection import get_connection

COLORS = {
    "main_bg":    "#F4F6F8",
    "white":      "#FFFFFF",
    "accent":     "#2980B9",
    "accent_dk":  "#2471A3",
    "text_dark":  "#2C3E50",
    "text_muted": "#7F8C8D",
    "border":     "#DDE1E7",
    "success":    "#27AE60",
    "input_bg":   "#FDFDFD",
    "label_bg":   "#F0F3F4",
}

def make_entry(parent, width=42):
    return tk.Entry(parent, width=width, font=("Segoe UI", 11),
                    bg=COLORS["input_bg"], fg=COLORS["text_dark"],
                    relief="flat", highlightthickness=1,
                    highlightbackground=COLORS["border"],
                    highlightcolor=COLORS["accent"],
                    insertbackground=COLORS["text_dark"])

def section_card(parent, title):
    outer = tk.Frame(parent, bg=COLORS["white"],
                     highlightbackground=COLORS["border"], highlightthickness=1)
    outer.pack(fill="x", padx=28, pady=(0, 16))
    header = tk.Frame(outer, bg=COLORS["label_bg"], height=38)
    header.pack(fill="x")
    header.pack_propagate(False)
    tk.Label(header, text=title, bg=COLORS["label_bg"],
             fg=COLORS["text_dark"], font=("Segoe UI", 11, "bold")
             ).pack(side="left", padx=16, pady=8)
    body = tk.Frame(outer, bg=COLORS["white"])
    body.pack(fill="x", padx=16, pady=12)
    return body


class SettingsPage(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORS["main_bg"], **kwargs)
        self._entries = {}
        self._load_settings()
        self._build()

    def _load_settings(self):
        conn = get_connection()
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
        conn.close()
        self._data = {row["key"]: row["value"] for row in rows}

    def _save(self):
        conn = get_connection()
        for key, entry in self._entries.items():
            value = entry.get().strip()
            conn.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (key, value))
        conn.commit()
        conn.close()
        self._save_btn.config(text="✅  Saved!", bg=COLORS["success"])
        self.after(2000, lambda: self._save_btn.config(text="💾  Save Settings", bg=COLORS["accent"]))

    def _add_row(self, parent, label_text, key, placeholder=""):
        row = tk.Frame(parent, bg=COLORS["white"])
        row.pack(fill="x", pady=5)
        tk.Label(row, text=label_text, bg=COLORS["white"], fg=COLORS["text_dark"],
                 font=("Segoe UI", 10), width=22, anchor="w").pack(side="left")
        entry = make_entry(row)
        entry.pack(side="left", padx=(8, 0), ipady=5)
        val = self._data.get(key, "")
        if val:
            entry.insert(0, val)
        elif placeholder:
            entry.insert(0, placeholder)
            entry.config(fg=COLORS["text_muted"])
            def _in(e, en=entry, ph=placeholder):
                if en.get() == ph: en.delete(0,"end"); en.config(fg=COLORS["text_dark"])
            def _out(e, en=entry, ph=placeholder):
                if not en.get(): en.insert(0,ph); en.config(fg=COLORS["text_muted"])
            entry.bind("<FocusIn>", _in)
            entry.bind("<FocusOut>", _out)
        self._entries[key] = entry

    def _build(self):
        canvas = tk.Canvas(self, bg=COLORS["main_bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        sf = tk.Frame(canvas, bg=COLORS["main_bg"])
        win = canvas.create_window((0,0), window=sf, anchor="nw")
        sf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        # Title
        t = tk.Frame(sf, bg=COLORS["main_bg"])
        t.pack(fill="x", padx=28, pady=(20,16))
        tk.Label(t, text="⚙️  Application Settings", bg=COLORS["main_bg"],
                 fg=COLORS["text_dark"], font=("Segoe UI", 16, "bold")).pack(side="left")

        # Sections
        b1 = section_card(sf, "🏢  Company Information")
        self._add_row(b1, "Company Name *",      "company_name",       "e.g. Al-Farooq Traders")
        self._add_row(b1, "Company Address",     "company_address",    "e.g. Shop 12, Main Market")
        self._add_row(b1, "Phone Number",        "company_phone",      "e.g. 0300-1234567")
        self._add_row(b1, "Email Address",       "company_email",      "e.g. info@company.com")
        self._add_row(b1, "Website (optional)",  "company_website",    "e.g. www.company.com")

        b2 = section_card(sf, "🧾  Invoice Settings")
        self._add_row(b2, "Invoice Prefix",      "invoice_prefix",     "INV")
        self._add_row(b2, "Currency Symbol",     "currency_symbol",    "Rs.")
        self._add_row(b2, "Tax Rate (%)",        "tax_rate",           "0")
        self._add_row(b2, "Invoice Footer Note", "invoice_footer",     "Thank you for your business!")

        b3 = section_card(sf, "🏦  Bank / Payment Details")
        self._add_row(b3, "Bank Name",           "bank_name",          "e.g. HBL / MCB / UBL")
        self._add_row(b3, "Account Title",       "bank_account_title", "e.g. Al-Farooq Traders")
        self._add_row(b3, "Account Number",      "bank_account_no",    "e.g. 1234-5678-9012")
        self._add_row(b3, "IBAN (optional)",     "bank_iban",          "e.g. PK36SCBL...")

        b4 = section_card(sf, "🖥️  App Preferences")
        self._add_row(b4, "Business Type",       "business_type",      "e.g. Retail / Wholesale")
        self._add_row(b4, "Financial Year Start","fy_start",           "e.g. January or July")

        # Save button
        br = tk.Frame(sf, bg=COLORS["main_bg"])
        br.pack(fill="x", padx=28, pady=(4,32))
        self._save_btn = tk.Button(br, text="💾  Save Settings",
                                   bg=COLORS["accent"], fg="white",
                                   font=("Segoe UI", 12, "bold"),
                                   relief="flat", cursor="hand2",
                                   padx=28, pady=10,
                                   activebackground=COLORS["accent_dk"],
                                   activeforeground="white",
                                   command=self._save)
        self._save_btn.pack(side="left")
        tk.Label(br, text="  Changes are saved to the local database",
                 bg=COLORS["main_bg"], fg=COLORS["text_muted"],
                 font=("Segoe UI", 9)).pack(side="left", padx=12)

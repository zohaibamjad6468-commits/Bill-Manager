import tkinter as tk
from tkinter import messagebox, ttk
import sys, os, datetime
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
    "warning":    "#E67E22",
    "danger":     "#E74C3C",
    "input_bg":   "#FDFDFD",
    "label_bg":   "#F0F3F4",
    "row_alt":    "#F8FAFB",
    "paid_bg":    "#EAFAF1",
    "unpaid_bg":  "#FEF9E7",
    "partial_bg": "#EBF5FB",
}

def styled_entry(parent, width=22):
    return tk.Entry(parent, width=width, font=("Segoe UI", 10),
                    bg=COLORS["input_bg"], fg=COLORS["text_dark"],
                    relief="flat", highlightthickness=1,
                    highlightbackground=COLORS["border"],
                    highlightcolor=COLORS["accent"],
                    insertbackground=COLORS["text_dark"])

def styled_btn(parent, text, command, color=None, fg="white", padx=14, pady=6):
    color = color or COLORS["accent"]
    return tk.Button(parent, text=text, command=command,
                     bg=color, fg=fg, font=("Segoe UI", 10, "bold"),
                     relief="flat", cursor="hand2", padx=padx, pady=pady,
                     activebackground=color, activeforeground=fg)


# ─────────────────────────────────────────────────────────────────────────────
#  INVOICE PDF GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def generate_invoice_pdf(invoice_id, filepath):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle, HRFlowable)
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    except ImportError:
        raise ImportError("reportlab not installed. Run: pip install reportlab")

    conn  = get_connection()
    inv   = conn.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()
    items = conn.execute("SELECT * FROM invoice_items WHERE invoice_id=?", (invoice_id,)).fetchall()
    cust  = conn.execute("SELECT * FROM customers WHERE id=?", (inv["customer_id"],)).fetchone()
    cfg   = {r["key"]:r["value"] for r in conn.execute("SELECT key,value FROM settings").fetchall()}
    conn.close()

    curr  = cfg.get("currency_symbol","Rs.")
    doc   = SimpleDocTemplate(filepath, pagesize=A4,
                              leftMargin=2*cm, rightMargin=2*cm,
                              topMargin=2*cm, bottomMargin=2*cm)
    ss    = getSampleStyleSheet()
    story = []

    NAVY  = colors.HexColor("#1E2A3A")
    BLUE  = colors.HexColor("#2980B9")
    LGREY = colors.HexColor("#F4F6F8")
    MGREY = colors.HexColor("#DDE1E7")
    GREEN = colors.HexColor("#27AE60")
    RED   = colors.HexColor("#E74C3C")
    ORANGE= colors.HexColor("#E67E22")

    def sty(**kw):
        return ParagraphStyle("c", parent=ss["Normal"], **kw)

    # ── Header ────────────────────────────────────────────────────────────────
    company_name  = cfg.get("company_name","Company")
    company_addr  = cfg.get("company_address","")
    company_phone = cfg.get("company_phone","")
    company_email = cfg.get("company_email","")

    hdr = Table([[
        Paragraph(f"<b>{company_name}</b><br/>"
                  f"<font size=8>{company_addr}</font><br/>"
                  f"<font size=8>{company_phone}   {company_email}</font>",
                  sty(fontSize=14, textColor=colors.white,
                      fontName="Helvetica-Bold", leading=20)),
        Paragraph(f"<b>INVOICE</b><br/>"
                  f"<font size=10>#{inv['invoice_number']}</font>",
                  sty(fontSize=18, textColor=colors.white,
                      fontName="Helvetica-Bold", alignment=2, leading=24))
    ]], colWidths=["60%","40%"])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), NAVY),
        ("PADDING",   (0,0),(-1,-1), 16),
        ("VALIGN",    (0,0),(-1,-1), "MIDDLE"),
    ]))
    story.append(hdr)
    story.append(Spacer(1, 0.4*cm))

    # Date + status
    sc = {"paid":GREEN,"unpaid":RED,"partial":ORANGE}.get(inv["status"], BLUE)
    info = Table([[
        Paragraph(f"Date: <b>{inv['date']}</b>",
                  sty(fontSize=9, textColor=colors.HexColor("#2C3E50"))),
        Paragraph(f"Status: <b>{inv['status'].upper()}</b>",
                  sty(fontSize=9, textColor=sc, fontName="Helvetica-Bold", alignment=2))
    ]], colWidths=["50%","50%"])
    info.setStyle(TableStyle([("PADDING",(0,0),(-1,-1),4)]))
    story.append(info)
    story.append(Spacer(1, 0.4*cm))

    # ── From / Bill To ────────────────────────────────────────────────────────
    cust_name  = cust["name"]    if cust else "—"
    cust_phone = cust["phone"]   if cust and cust["phone"]   else ""
    cust_addr  = cust["address"] if cust and cust["address"] else ""

    addr = Table([[
        [Paragraph("<b>FROM</b>",   sty(fontSize=8, textColor=colors.HexColor("#7F8C8D"))),
         Paragraph(company_name,    sty(fontSize=10,fontName="Helvetica-Bold",textColor=NAVY)),
         Paragraph(company_addr,    sty(fontSize=9, textColor=colors.HexColor("#2C3E50"))),
         Paragraph(company_phone,   sty(fontSize=9, textColor=colors.HexColor("#2C3E50"))),
         Paragraph(company_email,   sty(fontSize=9, textColor=colors.HexColor("#2C3E50"))),
        ],
        [Paragraph("<b>BILL TO</b>",sty(fontSize=8, textColor=colors.HexColor("#7F8C8D"))),
         Paragraph(cust_name,       sty(fontSize=10,fontName="Helvetica-Bold",textColor=NAVY)),
         Paragraph(cust_phone,      sty(fontSize=9, textColor=colors.HexColor("#2C3E50"))),
         Paragraph(cust_addr,       sty(fontSize=9, textColor=colors.HexColor("#2C3E50"))),
        ],
    ]], colWidths=["50%","50%"])
    addr.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), LGREY),
        ("PADDING",   (0,0),(-1,-1), 12),
        ("VALIGN",    (0,0),(-1,-1), "TOP"),
        ("LINEAFTER", (0,0),(0,-1),  0.5, MGREY),
    ]))
    story.append(addr)
    story.append(Spacer(1, 0.5*cm))

    # ── Items table ───────────────────────────────────────────────────────────
    rows = [["#","Description","Qty","Unit Price","Subtotal"]]
    for i, item in enumerate(items):
        rows.append([
            str(i+1), item["description"], str(item["quantity"]),
            f"{curr} {item['unit_price']:,.2f}",
            f"{curr} {item['subtotal']:,.2f}",
        ])
    itbl = Table(rows, colWidths=[1*cm, 8.5*cm, 2*cm, 3.5*cm, 3.5*cm])
    itbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  NAVY),
        ("TEXTCOLOR",     (0,0), (-1,0),  colors.white),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 9),
        ("ALIGN",         (2,0), (-1,-1), "RIGHT"),
        ("ALIGN",         (0,0), (0,-1),  "CENTER"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, LGREY]),
        ("GRID",          (0,0), (-1,-1), 0.5, MGREY),
        ("PADDING",       (0,0), (-1,-1), 7),
        ("TOPPADDING",    (0,0), (-1,0),  10),
        ("BOTTOMPADDING", (0,0), (-1,0),  10),
        ("FONTNAME",      (4,1), (4,-1),  "Helvetica-Bold"),
    ]))
    story.append(itbl)
    story.append(Spacer(1, 0.3*cm))

    # ── Totals ────────────────────────────────────────────────────────────────
    subtotal = sum(i["subtotal"] for i in items)
    balance  = inv["total_amount"] - inv["paid_amount"]
    tot_rows = [
        ["","Subtotal:",   f"{curr} {subtotal:,.2f}"],
        ["","Discount:",   f"{curr} {inv['discount']:,.2f}"],
        ["","TOTAL:",      f"{curr} {inv['total_amount']:,.2f}"],
        ["","Paid:",       f"{curr} {inv['paid_amount']:,.2f}"],
        ["","Balance Due:",f"{curr} {balance:,.2f}"],
    ]
    ttbl = Table(tot_rows, colWidths=[9*cm, 4*cm, 5.5*cm])
    ttbl.setStyle(TableStyle([
        ("FONTSIZE",   (0,0),  (-1,-1), 9),
        ("ALIGN",      (1,0),  (-1,-1), "RIGHT"),
        ("FONTNAME",   (1,2),  (-1,2),  "Helvetica-Bold"),
        ("FONTNAME",   (1,4),  (-1,4),  "Helvetica-Bold"),
        ("TEXTCOLOR",  (2,4),  (2,4),   RED if balance > 0 else GREEN),
        ("LINEABOVE",  (1,2),  (-1,2),  0.5, MGREY),
        ("LINEABOVE",  (1,4),  (-1,4),  1,   NAVY),
        ("PADDING",    (0,0),  (-1,-1), 5),
        ("TOPPADDING", (0,4),  (-1,4),  8),
    ]))
    story.append(ttbl)
    story.append(Spacer(1, 0.6*cm))

    # ── Bank details ──────────────────────────────────────────────────────────
    bank_parts = []
    if cfg.get("bank_name"):          bank_parts.append(f"Bank: {cfg['bank_name']}")
    if cfg.get("bank_account_title"): bank_parts.append(f"Account: {cfg['bank_account_title']}")
    if cfg.get("bank_account_no"):    bank_parts.append(f"No: {cfg['bank_account_no']}")
    if cfg.get("bank_iban"):          bank_parts.append(f"IBAN: {cfg['bank_iban']}")
    if bank_parts:
        story.append(HRFlowable(width="100%", thickness=0.5, color=MGREY))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph("<b>Payment Details:</b>   " + "   |   ".join(bank_parts),
                               sty(fontSize=8, textColor=colors.HexColor("#2C3E50"))))
        story.append(Spacer(1, 0.3*cm))

    # ── Notes ─────────────────────────────────────────────────────────────────
    if inv["notes"]:
        story.append(Paragraph(f"<b>Notes:</b> {inv['notes']}",
                               sty(fontSize=9, textColor=colors.HexColor("#555555"))))
        story.append(Spacer(1, 0.3*cm))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=MGREY))
    story.append(Paragraph(cfg.get("invoice_footer","Thank you for your business!"),
                           sty(fontSize=9, textColor=BLUE, alignment=1)))

    doc.build(story)


# ─────────────────────────────────────────────────────────────────────────────
#  ADD CUSTOMER WINDOW
# ─────────────────────────────────────────────────────────────────────────────

class AddCustomerWindow(tk.Toplevel):
    def __init__(self, parent, on_saved=None):
        super().__init__(parent)
        self.on_saved = on_saved
        self.title("Add New Customer")
        self.geometry("580x560")
        self.resizable(False, False)
        self.configure(bg=COLORS["main_bg"])
        self.grab_set()
        self._build()

    def _build(self):
        h = tk.Frame(self, bg=COLORS["success"], height=44)
        h.pack(fill="x"); h.pack_propagate(False)
        tk.Label(h, text="  New Customer", bg=COLORS["success"], fg="white",
                 font=("Segoe UI", 12, "bold")).pack(side="left", padx=14, pady=8)

        f = tk.Frame(self, bg=COLORS["main_bg"])
        f.pack(fill="both", expand=True, padx=20, pady=12)

        self._vars = {}
        fields = [
            ("Name *",  "name",    "Customer or Business name"),
            ("Phone",   "phone",   "e.g. 0300-1234567"),
            ("Address", "address", "City / Area"),
            ("Email",   "email",   "optional"),
        ]
        for label, key, ph in fields:
            tk.Label(f, text=label, bg=COLORS["main_bg"],
                     fg=COLORS["text_dark"], font=("Segoe UI", 10)).pack(anchor="w", pady=(6,0))
            e = styled_entry(f, width=44)
            e.insert(0, ph)
            e.config(fg=COLORS["text_muted"])
            def _fi(ev, en=e, p=ph):
                if en.get() == p: en.delete(0,"end"); en.config(fg=COLORS["text_dark"])
            def _fo(ev, en=e, p=ph):
                if not en.get(): en.insert(0,p); en.config(fg=COLORS["text_muted"])
            e.bind("<FocusIn>",  _fi)
            e.bind("<FocusOut>", _fo)
            e.pack(fill="x", ipady=5)
            self._vars[key] = e

        styled_btn(f, "  Save Customer", self._save, color=COLORS["success"]).pack(pady=12)

    def _save(self):
        name = self._vars["name"].get().strip()
        if not name or name == "Customer or Business name":
            messagebox.showwarning("Required", "Please enter a customer name.", parent=self)
            return
        placeholders = {"e.g. 0300-1234567", "City / Area", "optional"}
        phone   = self._vars["phone"].get().strip()
        address = self._vars["address"].get().strip()
        email   = self._vars["email"].get().strip()
        phone   = "" if phone   in placeholders else phone
        address = "" if address in placeholders else address
        email   = "" if email   in placeholders else email

        conn = get_connection()
        conn.execute("INSERT INTO customers (name,phone,address,email) VALUES (?,?,?,?)",
                     (name, phone, address, email))
        conn.commit(); conn.close()
        if self.on_saved: self.on_saved()
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
#  CUSTOMER SELECTOR POPUP
# ─────────────────────────────────────────────────────────────────────────────

class CustomerPopup(tk.Toplevel):
    def __init__(self, parent, on_select):
        super().__init__(parent)
        self.on_select = on_select
        self.title("Select Customer")
        self.geometry("580x560")
        self.resizable(False, False)
        self.configure(bg=COLORS["main_bg"])
        self.grab_set()
        self._build()
        self._load()

    def _build(self):
        h = tk.Frame(self, bg=COLORS["accent"], height=48)
        h.pack(fill="x"); h.pack_propagate(False)
        tk.Label(h, text="  Select Customer", bg=COLORS["accent"], fg="white",
                 font=("Segoe UI", 13, "bold")).pack(side="left", padx=16, pady=10)

        sf = tk.Frame(self, bg=COLORS["white"],
                      highlightbackground=COLORS["border"], highlightthickness=1)
        sf.pack(fill="x", padx=16, pady=(12,4))
        tk.Label(sf, text="Search:", bg=COLORS["white"],
                 font=("Segoe UI", 10)).pack(side="left", padx=8)
        self._search_var = tk.StringVar()
        self._search_var.trace("w", lambda *a: self._load())
        tk.Entry(sf, textvariable=self._search_var, font=("Segoe UI", 11),
                 bg=COLORS["white"], fg=COLORS["text_dark"], relief="flat",
                 insertbackground=COLORS["text_dark"]
                 ).pack(side="left", fill="x", expand=True, ipady=7, padx=4)

        lf = tk.Frame(self, bg=COLORS["white"],
                      highlightbackground=COLORS["border"], highlightthickness=1)
        lf.pack(fill="both", expand=True, padx=16, pady=4)

        cols = ("Name","Phone","Address")
        self._tree = ttk.Treeview(lf, columns=cols, show="headings",
                                  height=9, selectmode="browse")
        for col, w in zip(cols, [190,130,170]):
            self._tree.heading(col, text=col)
            self._tree.column(col, width=w, anchor="w")
        sb = ttk.Scrollbar(lf, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True)
        self._tree.bind("<Double-1>", lambda e: self._select())

        br = tk.Frame(self, bg=COLORS["main_bg"])
        br.pack(fill="x", padx=16, pady=8)
        styled_btn(br, "  Select", self._select).pack(side="left", padx=(0,8))
        styled_btn(br, "  Add New", self._add_new, color=COLORS["success"]).pack(side="left")
        styled_btn(br, "Cancel",    self.destroy,  color=COLORS["danger"]).pack(side="right")

    def _load(self):
        q = self._search_var.get().strip()
        conn = get_connection()
        if q:
            rows = conn.execute("SELECT id,name,phone,address FROM customers WHERE name LIKE ? ORDER BY name", (f"%{q}%",)).fetchall()
        else:
            rows = conn.execute("SELECT id,name,phone,address FROM customers ORDER BY name").fetchall()
        conn.close()
        self._tree.delete(*self._tree.get_children())
        for r in rows:
            self._tree.insert("", "end", iid=str(r["id"]),
                              values=(r["name"], r["phone"] or "", r["address"] or ""))

    def _select(self):
        sel = self._tree.focus()
        if not sel:
            messagebox.showwarning("Select", "Please select a customer first.", parent=self); return
        conn = get_connection()
        row = conn.execute("SELECT * FROM customers WHERE id=?", (int(sel),)).fetchone()
        conn.close()
        self.on_select(dict(row))
        self.destroy()

    def _add_new(self):
        AddCustomerWindow(self, on_saved=self._load)


# ─────────────────────────────────────────────────────────────────────────────
#  INVOICE FORM (Create / Edit)
# ─────────────────────────────────────────────────────────────────────────────

class InvoiceForm(tk.Toplevel):
    def __init__(self, parent, on_saved, invoice_id=None):
        super().__init__(parent)
        self.on_saved   = on_saved
        self.invoice_id = invoice_id
        self._customer  = None
        self._item_rows = []

        self.title("Edit Invoice" if invoice_id else "New Invoice")
        self.geometry("880x700")
        self.minsize(780, 600)
        self.configure(bg=COLORS["main_bg"])
        self.grab_set()

        self._load_settings()
        self._build()
        if invoice_id:
            self._load_invoice()
        else:
            self._auto_invoice_number()

    def _load_settings(self):
        conn = get_connection()
        self._cfg = {r["key"]:r["value"] for r in conn.execute("SELECT key,value FROM settings").fetchall()}
        conn.close()

    def _auto_invoice_number(self):
        conn = get_connection()
        count = conn.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
        conn.close()
        prefix = self._cfg.get("invoice_prefix","INV")
        year   = datetime.date.today().year
        self._inv_num_var.set(f"{prefix}-{year}-{count+1:04d}")

    def _build(self):
        # Header
        h = tk.Frame(self, bg=COLORS["accent"], height=50)
        h.pack(fill="x"); h.pack_propagate(False)
        tk.Label(h, text="Edit Invoice" if self.invoice_id else "  Create New Invoice",
                 bg=COLORS["accent"], fg="white",
                 font=("Segoe UI",14,"bold")).pack(side="left", padx=18, pady=10)

        # Scrollable canvas
        canvas = tk.Canvas(self, bg=COLORS["main_bg"], highlightthickness=0)
        sb = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        body = tk.Frame(canvas, bg=COLORS["main_bg"])
        win  = canvas.create_window((0,0), window=body, anchor="nw")
        body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120),"units"))

        # ── Invoice # / Date / Status ─────────────────────────────────────────
        r1 = tk.Frame(body, bg=COLORS["main_bg"])
        r1.pack(fill="x", padx=20, pady=(14,6))

        def lframe(parent, title):
            f = tk.Frame(parent, bg=COLORS["white"],
                         highlightbackground=COLORS["border"], highlightthickness=1)
            f.pack(side="left", fill="x", expand=True, padx=(0,10))
            tk.Label(f, text=title, bg=COLORS["label_bg"], fg=COLORS["text_muted"],
                     font=("Segoe UI",8,"bold")).pack(fill="x", padx=0)
            inner = tk.Frame(f, bg=COLORS["white"])
            inner.pack(padx=10, pady=6)
            return inner

        self._inv_num_var = tk.StringVar()
        inv_f = lframe(r1, "  INVOICE NUMBER")
        inv_e = tk.Entry(inv_f, textvariable=self._inv_num_var, width=20,
                         font=("Segoe UI",11), bg=COLORS["input_bg"],
                         fg=COLORS["text_dark"], relief="flat",
                         highlightthickness=1, highlightbackground=COLORS["border"])
        inv_e.pack(ipady=5)

        self._date_var = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        date_f = lframe(r1, "  DATE (YYYY-MM-DD)")
        tk.Entry(date_f, textvariable=self._date_var, width=14,
                 font=("Segoe UI",11), bg=COLORS["input_bg"],
                 fg=COLORS["text_dark"], relief="flat",
                 highlightthickness=1, highlightbackground=COLORS["border"]
                 ).pack(ipady=5)

        self._status_var = tk.StringVar(value="unpaid")
        stat_f = lframe(r1, "  PAYMENT STATUS")
        ttk.Combobox(stat_f, textvariable=self._status_var, width=12,
                     values=["unpaid","paid","partial"],
                     font=("Segoe UI",11), state="readonly").pack(ipady=3)

        # ── Customer ──────────────────────────────────────────────────────────
        r2 = tk.Frame(body, bg=COLORS["main_bg"])
        r2.pack(fill="x", padx=20, pady=6)
        cust_card = tk.Frame(r2, bg=COLORS["white"],
                             highlightbackground=COLORS["border"], highlightthickness=1)
        cust_card.pack(fill="x")
        tk.Label(cust_card, text="  CUSTOMER", bg=COLORS["label_bg"],
                 fg=COLORS["text_muted"], font=("Segoe UI",8,"bold")).pack(fill="x")
        inner2 = tk.Frame(cust_card, bg=COLORS["white"])
        inner2.pack(fill="x", padx=10, pady=8)
        self._cust_lbl = tk.Label(inner2, text="  No customer selected — click button to choose",
                                  bg=COLORS["white"], fg=COLORS["text_muted"],
                                  font=("Segoe UI",10))
        self._cust_lbl.pack(side="left", fill="x", expand=True)
        styled_btn(inner2, "  Select Customer",
                   lambda: CustomerPopup(self, self._on_customer),
                   color=COLORS["accent"]).pack(side="right")

        # ── Items header ──────────────────────────────────────────────────────
        r3 = tk.Frame(body, bg=COLORS["main_bg"])
        r3.pack(fill="x", padx=20, pady=(10,2))
        tk.Label(r3, text="  Items / Services", bg=COLORS["main_bg"],
                 fg=COLORS["text_dark"], font=("Segoe UI",11,"bold")).pack(side="left")
        styled_btn(r3, "  Add Item", self._add_row,
                   color=COLORS["success"]).pack(side="right")

        # Table column headers
        thead = tk.Frame(body, bg="#34495E")
        thead.pack(fill="x", padx=20)
        for txt, w in [("  #",4),("Description",36),("Qty",8),("Unit Price",12),("Subtotal",12),("",4)]:
            tk.Label(thead, text=txt, bg="#34495E", fg="white",
                     font=("Segoe UI",10,"bold"), width=int(w), anchor="w"
                     ).pack(side="left", padx=4, pady=7)

        # Items container
        self._items_frame = tk.Frame(body, bg=COLORS["white"],
                                     highlightbackground=COLORS["border"],
                                     highlightthickness=1)
        self._items_frame.pack(fill="x", padx=20)

        # ── Totals + Notes ────────────────────────────────────────────────────
        bot = tk.Frame(body, bg=COLORS["main_bg"])
        bot.pack(fill="x", padx=20, pady=(10,6))

        # Notes left
        notes_card = tk.Frame(bot, bg=COLORS["white"],
                               highlightbackground=COLORS["border"], highlightthickness=1)
        notes_card.pack(side="left", fill="both", expand=True, padx=(0,12))
        tk.Label(notes_card, text="  NOTES", bg=COLORS["label_bg"],
                 fg=COLORS["text_muted"], font=("Segoe UI",8,"bold")).pack(fill="x")
        self._notes = tk.Text(notes_card, height=5, font=("Segoe UI",10),
                              bg=COLORS["input_bg"], fg=COLORS["text_dark"],
                              relief="flat", wrap="word")
        self._notes.pack(padx=8, pady=8, fill="both", expand=True)

        # Totals right
        totals_card = tk.Frame(bot, bg=COLORS["white"],
                                highlightbackground=COLORS["border"], highlightthickness=1)
        totals_card.pack(side="right", fill="y", ipadx=6)
        tk.Label(totals_card, text="  TOTALS", bg=COLORS["label_bg"],
                 fg=COLORS["text_muted"], font=("Segoe UI",8,"bold")).pack(fill="x")
        tf = tk.Frame(totals_card, bg=COLORS["white"])
        tf.pack(padx=14, pady=10)

        curr = self._cfg.get("currency_symbol","Rs.")

        def trow(label, bold=False):
            r = tk.Frame(tf, bg=COLORS["white"]); r.pack(fill="x", pady=3)
            w = "bold" if bold else "normal"
            tk.Label(r, text=label, bg=COLORS["white"], fg=COLORS["text_dark"],
                     font=("Segoe UI",10,w), width=13, anchor="w").pack(side="left")
            lbl = tk.Label(r, text=f"{curr} 0.00", bg=COLORS["white"],
                           fg=COLORS["text_dark"], font=("Segoe UI",10,w),
                           width=14, anchor="e")
            lbl.pack(side="right"); return lbl

        self._lbl_sub   = trow("Subtotal:")

        disc_row = tk.Frame(tf, bg=COLORS["white"]); disc_row.pack(fill="x", pady=3)
        tk.Label(disc_row, text="Discount:", bg=COLORS["white"], fg=COLORS["text_dark"],
                 font=("Segoe UI",10), width=13, anchor="w").pack(side="left")
        self._disc_e = tk.Entry(disc_row, width=10, font=("Segoe UI",10),
                                bg=COLORS["input_bg"], relief="flat",
                                highlightthickness=1, highlightbackground=COLORS["border"])
        self._disc_e.insert(0,"0"); self._disc_e.pack(side="right", ipady=3)
        self._disc_e.bind("<KeyRelease>", lambda e: self._recalc())

        tax = float(self._cfg.get("tax_rate","0") or 0)
        self._lbl_tax = trow(f"Tax ({tax}%):") if tax > 0 else None

        tk.Frame(tf, bg=COLORS["border"], height=1).pack(fill="x", pady=4)
        self._lbl_total = trow("TOTAL:", bold=True)

        paid_row = tk.Frame(tf, bg=COLORS["white"]); paid_row.pack(fill="x", pady=3)
        tk.Label(paid_row, text="Paid Amount:", bg=COLORS["white"], fg=COLORS["text_dark"],
                 font=("Segoe UI",10), width=13, anchor="w").pack(side="left")
        self._paid_e = tk.Entry(paid_row, width=10, font=("Segoe UI",10),
                                bg=COLORS["input_bg"], relief="flat",
                                highlightthickness=1, highlightbackground=COLORS["border"])
        self._paid_e.insert(0,"0"); self._paid_e.pack(side="right", ipady=3)

        # ── Save / Cancel ─────────────────────────────────────────────────────
        save_row = tk.Frame(body, bg=COLORS["main_bg"])
        save_row.pack(fill="x", padx=20, pady=(4,20))
        styled_btn(save_row, "  Save Invoice", self._save,
                   color=COLORS["success"], padx=22, pady=10).pack(side="left")
        styled_btn(save_row, "Cancel", self.destroy,
                   color=COLORS["danger"], padx=14, pady=10).pack(side="left", padx=10)

        # Start with one blank row
        self._add_row()

    def _on_customer(self, c):
        self._customer = c
        self._cust_lbl.config(
            text=f"  {c['name']}    |    {c.get('phone','') or '—'}    |    {c.get('address','') or '—'}",
            fg=COLORS["text_dark"])

    def _add_row(self, desc="", qty="1", price="0"):
        idx = len(self._item_rows) + 1
        bg  = COLORS["white"] if idx % 2 == 1 else COLORS["row_alt"]
        row = tk.Frame(self._items_frame, bg=bg)
        row.pack(fill="x", pady=1)

        tk.Label(row, text=str(idx), bg=bg, fg=COLORS["text_muted"],
                 font=("Segoe UI",10), width=4).pack(side="left", padx=4, pady=6)

        desc_e = tk.Entry(row, width=36, font=("Segoe UI",10),
                          bg=bg, fg=COLORS["text_dark"], relief="flat",
                          highlightthickness=1, highlightbackground=COLORS["border"])
        desc_e.insert(0, desc); desc_e.pack(side="left", padx=4, ipady=5)

        qty_e = tk.Entry(row, width=8, font=("Segoe UI",10), justify="center",
                         bg=bg, fg=COLORS["text_dark"], relief="flat",
                         highlightthickness=1, highlightbackground=COLORS["border"])
        qty_e.insert(0, qty); qty_e.pack(side="left", padx=4, ipady=5)

        price_e = tk.Entry(row, width=12, font=("Segoe UI",10), justify="right",
                           bg=bg, fg=COLORS["text_dark"], relief="flat",
                           highlightthickness=1, highlightbackground=COLORS["border"])
        price_e.insert(0, price); price_e.pack(side="left", padx=4, ipady=5)

        sub_lbl = tk.Label(row, text="0.00", bg=bg, fg=COLORS["text_dark"],
                           font=("Segoe UI",10), width=12, anchor="e")
        sub_lbl.pack(side="left", padx=4)

        def calc(*_):
            try:
                s = float(qty_e.get() or 0) * float(price_e.get() or 0)
                sub_lbl.config(text=f"{s:,.2f}")
            except ValueError:
                sub_lbl.config(text="0.00")
            self._recalc()

        qty_e.bind("<KeyRelease>",   calc)
        price_e.bind("<KeyRelease>", calc)

        tk.Button(row, text="x", bg=bg, fg=COLORS["danger"],
                  font=("Segoe UI",10,"bold"), relief="flat", cursor="hand2",
                  width=3, command=lambda r=row: self._del_row(r)
                  ).pack(side="left", padx=4)

        self._item_rows.append({"frame":row,"desc":desc_e,"qty":qty_e,"price":price_e,"sub":sub_lbl})

    def _del_row(self, frame):
        frame.destroy()
        self._item_rows = [r for r in self._item_rows if r["frame"].winfo_exists()]
        self._recalc()

    def _recalc(self):
        curr = self._cfg.get("currency_symbol","Rs.")
        sub = sum(
            float(r["qty"].get() or 0) * float(r["price"].get() or 0)
            for r in self._item_rows if r["frame"].winfo_exists()
        )
        try:    disc = float(self._disc_e.get() or 0)
        except: disc = 0
        tax_rate = float(self._cfg.get("tax_rate","0") or 0)
        tax   = (sub - disc) * tax_rate / 100
        total = sub - disc + tax
        self._lbl_sub.config(text=f"{curr} {sub:,.2f}")
        if self._lbl_tax: self._lbl_tax.config(text=f"{curr} {tax:,.2f}")
        self._lbl_total.config(text=f"{curr} {total:,.2f}")

    def _save(self):
        inv_num = self._inv_num_var.get().strip()
        date    = self._date_var.get().strip()
        status  = self._status_var.get()
        notes   = self._notes.get("1.0","end").strip()

        if not inv_num:
            messagebox.showwarning("Required", "Invoice number is required.", parent=self); return
        if not self._customer:
            messagebox.showwarning("Required", "Please select a customer.", parent=self); return

        items = []
        for r in self._item_rows:
            if not r["frame"].winfo_exists(): continue
            d = r["desc"].get().strip()
            if not d: continue
            try:
                q = float(r["qty"].get());  p = float(r["price"].get())
            except ValueError:
                messagebox.showwarning("Invalid", "Enter valid numbers for Qty and Price.", parent=self); return
            items.append((d, q, p, q*p))

        if not items:
            messagebox.showwarning("Required", "Please add at least one item.", parent=self); return

        sub = sum(i[3] for i in items)
        try:    disc = float(self._disc_e.get() or 0)
        except: disc = 0
        tax_rate = float(self._cfg.get("tax_rate","0") or 0)
        total = sub - disc + (sub - disc) * tax_rate / 100
        try:    paid = float(self._paid_e.get() or 0)
        except: paid = 0

        conn = get_connection()
        try:
            if self.invoice_id:
                conn.execute("""UPDATE invoices SET invoice_number=?,customer_id=?,date=?,
                    total_amount=?,paid_amount=?,discount=?,notes=?,status=? WHERE id=?""",
                    (inv_num,self._customer["id"],date,total,paid,disc,notes,status,self.invoice_id))
                conn.execute("DELETE FROM invoice_items WHERE invoice_id=?", (self.invoice_id,))
                iid = self.invoice_id
            else:
                cur = conn.execute("""INSERT INTO invoices
                    (invoice_number,customer_id,date,total_amount,paid_amount,discount,notes,status)
                    VALUES (?,?,?,?,?,?,?,?)""",
                    (inv_num,self._customer["id"],date,total,paid,disc,notes,status))
                iid = cur.lastrowid
            for d,q,p,s in items:
                conn.execute("INSERT INTO invoice_items (invoice_id,description,quantity,unit_price,subtotal) VALUES (?,?,?,?,?)",
                             (iid,d,q,p,s))
            conn.commit()
        except Exception as ex:
            conn.rollback()
            messagebox.showerror("Error", str(ex), parent=self); return
        finally:
            conn.close()

        messagebox.showinfo("Saved", f"Invoice {inv_num} saved!", parent=self)
        self.on_saved(); self.destroy()

    def _load_invoice(self):
        conn = get_connection()
        inv   = conn.execute("SELECT * FROM invoices WHERE id=?", (self.invoice_id,)).fetchone()
        items = conn.execute("SELECT * FROM invoice_items WHERE invoice_id=?", (self.invoice_id,)).fetchall()
        cust  = conn.execute("SELECT * FROM customers WHERE id=?", (inv["customer_id"],)).fetchone()
        conn.close()
        if not inv: return
        self._inv_num_var.set(inv["invoice_number"])
        self._date_var.set(inv["date"])
        self._status_var.set(inv["status"])
        self._disc_e.delete(0,"end"); self._disc_e.insert(0, str(inv["discount"]))
        self._paid_e.delete(0,"end"); self._paid_e.insert(0, str(inv["paid_amount"]))
        if inv["notes"]: self._notes.insert("1.0", inv["notes"])
        if cust: self._on_customer(dict(cust))
        for r in self._item_rows: r["frame"].destroy()
        self._item_rows.clear()
        for i in items: self._add_row(i["description"], str(i["quantity"]), str(i["unit_price"]))
        self._recalc()


# ─────────────────────────────────────────────────────────────────────────────
#  INVOICE DETAIL VIEW
# ─────────────────────────────────────────────────────────────────────────────

class InvoiceDetailWindow(tk.Toplevel):
    def __init__(self, parent, invoice_id, on_edit):
        super().__init__(parent)
        self.invoice_id = invoice_id
        self.on_edit    = on_edit
        self.title("Invoice Detail")
        self.geometry("620x600")
        self.configure(bg=COLORS["white"])
        self.grab_set()
        self._build()

    def _build(self):
        conn = get_connection()
        inv   = conn.execute("SELECT * FROM invoices WHERE id=?", (self.invoice_id,)).fetchone()
        items = conn.execute("SELECT * FROM invoice_items WHERE invoice_id=?", (self.invoice_id,)).fetchall()
        cust  = conn.execute("SELECT * FROM customers WHERE id=?", (inv["customer_id"],)).fetchone()
        cfg   = {r["key"]:r["value"] for r in conn.execute("SELECT key,value FROM settings").fetchall()}
        conn.close()
        curr = cfg.get("currency_symbol","Rs.")

        # Header
        h = tk.Frame(self, bg=COLORS["accent"], height=56)
        h.pack(fill="x"); h.pack_propagate(False)
        tk.Label(h, text=f"  Invoice {inv['invoice_number']}", bg=COLORS["accent"],
                 fg="white", font=("Segoe UI",14,"bold")).pack(side="left", padx=18, pady=12)
        sc = {"paid":COLORS["success"],"unpaid":COLORS["warning"],"partial":COLORS["accent"]}.get(inv["status"],COLORS["text_muted"])
        tk.Label(h, text=f"  {inv['status'].upper()}  ", bg=sc, fg="white",
                 font=("Segoe UI",10,"bold")).pack(side="right", padx=18, pady=16)

        body = tk.Frame(self, bg=COLORS["white"])
        body.pack(fill="both", expand=True, padx=24, pady=14)

        # From / To
        top = tk.Frame(body, bg=COLORS["white"]); top.pack(fill="x", pady=(0,10))
        for title, lines in [
            ("FROM", [cfg.get("company_name","—"), cfg.get("company_address",""), cfg.get("company_phone",""), f"Date: {inv['date']}"]),
            ("BILL TO", [cust["name"] if cust else "—", cust["phone"] if cust else "", cust["address"] if cust else ""]),
        ]:
            f = tk.Frame(top, bg=COLORS["label_bg"],
                         highlightbackground=COLORS["border"], highlightthickness=1)
            f.pack(side="left", fill="both", expand=True, padx=(0,10))
            tk.Label(f, text=title, bg=COLORS["label_bg"], fg=COLORS["text_muted"],
                     font=("Segoe UI",9,"bold")).pack(anchor="w", padx=10, pady=(8,2))
            for l in lines:
                if l: tk.Label(f, text=l, bg=COLORS["label_bg"], fg=COLORS["text_dark"],
                               font=("Segoe UI",10)).pack(anchor="w", padx=10, pady=1)
            tk.Label(f, text="").pack(pady=3)

        # Items
        th = tk.Frame(body, bg="#34495E"); th.pack(fill="x")
        for t, w in [("Description",30),("Qty",6),("Price",12),("Subtotal",12)]:
            tk.Label(th, text=t, bg="#34495E", fg="white",
                     font=("Segoe UI",10,"bold"), width=w, anchor="w"
                     ).pack(side="left", padx=6, pady=6)

        items_f = tk.Frame(body, bg=COLORS["white"],
                           highlightbackground=COLORS["border"], highlightthickness=1)
        items_f.pack(fill="x")
        for i, item in enumerate(items):
            bg = COLORS["row_alt"] if i%2 else COLORS["white"]
            r = tk.Frame(items_f, bg=bg); r.pack(fill="x")
            tk.Label(r, text=item["description"], bg=bg, fg=COLORS["text_dark"],
                     font=("Segoe UI",10), width=30, anchor="w").pack(side="left",padx=6,pady=5)
            tk.Label(r, text=str(item["quantity"]), bg=bg, fg=COLORS["text_dark"],
                     font=("Segoe UI",10), width=6, anchor="center").pack(side="left",padx=6)
            tk.Label(r, text=f"{curr} {item['unit_price']:,.2f}", bg=bg, fg=COLORS["text_dark"],
                     font=("Segoe UI",10), width=12, anchor="e").pack(side="left",padx=6)
            tk.Label(r, text=f"{curr} {item['subtotal']:,.2f}", bg=bg,
                     fg=COLORS["text_dark"], font=("Segoe UI",10,"bold"),
                     width=12, anchor="e").pack(side="left",padx=6)

        # Totals
        tf = tk.Frame(body, bg=COLORS["white"]); tf.pack(anchor="e", pady=8)
        balance = inv["total_amount"] - inv["paid_amount"]
        for lbl, val, bold in [
            ("Subtotal:",  f"{curr} {sum(i['subtotal'] for i in items):,.2f}", False),
            ("Discount:",  f"{curr} {inv['discount']:,.2f}",                   False),
            ("Total:",     f"{curr} {inv['total_amount']:,.2f}",               True),
            ("Paid:",      f"{curr} {inv['paid_amount']:,.2f}",                False),
            ("Balance:",   f"{curr} {balance:,.2f}",                           True),
        ]:
            r = tk.Frame(tf, bg=COLORS["white"]); r.pack(fill="x", pady=2)
            w = "bold" if bold else "normal"
            fg = COLORS["danger"] if lbl=="Balance:" and balance>0 else COLORS["text_dark"]
            tk.Label(r, text=lbl, bg=COLORS["white"], fg=fg,
                     font=("Segoe UI",10,w), width=12, anchor="w").pack(side="left")
            tk.Label(r, text=val, bg=COLORS["white"], fg=fg,
                     font=("Segoe UI",10,w), width=16, anchor="e").pack(side="right")

        # Buttons
        br = tk.Frame(self, bg=COLORS["main_bg"]); br.pack(fill="x", padx=24, pady=10)
        styled_btn(br, "  Edit Invoice",
                   lambda: [self.destroy(), self.on_edit()],
                   color=COLORS["accent"]).pack(side="left", padx=(0,10))
        styled_btn(br, "  Print / Save PDF",
                   self._print_pdf, color="#8E44AD").pack(side="left", padx=(0,10))
        styled_btn(br, "Close", self.destroy, color=COLORS["danger"]).pack(side="left")

    def _print_pdf(self):
        from tkinter import filedialog
        conn = get_connection()
        inv = conn.execute("SELECT invoice_number FROM invoices WHERE id=?",
                           (self.invoice_id,)).fetchone()
        conn.close()
        default_name = f"Invoice_{inv['invoice_number']}.pdf"
        filepath = filedialog.asksaveasfilename(
            title="Save Invoice PDF",
            initialfile=default_name,
            defaultextension=".pdf",
            filetypes=[("PDF Files","*.pdf"),("All Files","*.*")]
        )
        if not filepath:
            return
        try:
            generate_invoice_pdf(self.invoice_id, filepath)
            if messagebox.askyesno("PDF Saved",
                    f"Invoice PDF saved to:\n{filepath}\n\nOpen it now?", parent=self):
                import os, sys
                if os.name == "nt":
                    os.startfile(filepath)
                elif sys.platform == "darwin":
                    os.system(f'open "{filepath}"')
                else:
                    os.system(f'xdg-open "{filepath}"')
        except Exception as ex:
            messagebox.showerror("Error", f"Could not generate PDF:\n{str(ex)}", parent=self)


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN INVOICES PAGE
# ─────────────────────────────────────────────────────────────────────────────

class InvoicesPage(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORS["main_bg"], **kwargs)
        self._build()
        self._load()

    def _build(self):
        # Action bar
        bar = tk.Frame(self, bg=COLORS["white"],
                       highlightbackground=COLORS["border"], highlightthickness=1)
        bar.pack(fill="x")
        styled_btn(bar, "  New Invoice", self._new_invoice,
                   color=COLORS["success"], padx=18, pady=10).pack(side="left", padx=12, pady=8)

        sf = tk.Frame(bar, bg=COLORS["white"],
                      highlightbackground=COLORS["border"], highlightthickness=1)
        sf.pack(side="left", padx=8, pady=8)
        tk.Label(sf, text="Search:", bg=COLORS["white"],
                 font=("Segoe UI",10)).pack(side="left", padx=6)
        self._search_var = tk.StringVar()
        self._search_var.trace("w", lambda *a: self._load())
        tk.Entry(sf, textvariable=self._search_var, width=22,
                 font=("Segoe UI",10), bg=COLORS["white"],
                 fg=COLORS["text_dark"], relief="flat",
                 insertbackground=COLORS["text_dark"]
                 ).pack(side="left", ipady=5, padx=4)

        # Status filter
        self._filter_var = tk.StringVar(value="all")
        for val, lbl in [("all","All"),("paid","Paid"),("unpaid","Unpaid"),("partial","Partial")]:
            tk.Radiobutton(bar, text=lbl, variable=self._filter_var, value=val,
                           bg=COLORS["white"], fg=COLORS["text_dark"],
                           font=("Segoe UI",10), activebackground=COLORS["white"],
                           selectcolor=COLORS["white"],
                           command=self._load).pack(side="left", padx=6)

        # Summary bar
        self._summary_lbl = tk.Label(self, text="",
                                     bg=COLORS["label_bg"], fg=COLORS["text_muted"],
                                     font=("Segoe UI",10))
        self._summary_lbl.pack(fill="x", padx=0, pady=0, ipady=6)

        # Treeview
        style = ttk.Style()
        style.configure("Treeview",         rowheight=32, font=("Segoe UI",10))
        style.configure("Treeview.Heading", font=("Segoe UI",10,"bold"))

        cols = ("Invoice #","Customer","Date","Total","Paid","Balance","Status")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        for col, w in zip(cols, [120,185,100,115,115,115,90]):
            self._tree.heading(col, text=col, command=lambda c=col: self._sort(c))
            self._tree.column(col, width=w, anchor="w")

        self._tree.tag_configure("paid",    background=COLORS["paid_bg"])
        self._tree.tag_configure("unpaid",  background=COLORS["unpaid_bg"])
        self._tree.tag_configure("partial", background=COLORS["partial_bg"])

        vsb = ttk.Scrollbar(self, orient="vertical",   command=self._tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self._tree.pack(fill="both", expand=True)

        self._tree.bind("<Double-1>", lambda e: self._view_detail())

        # Right-click menu
        self._menu = tk.Menu(self, tearoff=0)
        self._menu.add_command(label="View Details",     command=self._view_detail)
        self._menu.add_command(label="Edit Invoice",     command=self._edit_invoice)
        self._menu.add_separator()
        self._menu.add_command(label="Mark as Paid",     command=lambda: self._set_status("paid"))
        self._menu.add_command(label="Mark as Unpaid",   command=lambda: self._set_status("unpaid"))
        self._menu.add_separator()
        self._menu.add_command(label="Delete Invoice",   command=self._delete_invoice)
        self._tree.bind("<Button-3>", self._show_menu)

        self._sort_col = None; self._sort_rev = False

    def _load(self):
        q  = self._search_var.get().strip()
        fv = self._filter_var.get()
        conn = get_connection()
        sql = """SELECT i.id,i.invoice_number,c.name as customer,i.date,
                        i.total_amount,i.paid_amount,
                        i.total_amount-i.paid_amount as balance,i.status
                 FROM invoices i LEFT JOIN customers c ON i.customer_id=c.id
                 WHERE 1=1"""
        params = []
        if fv != "all": sql += " AND i.status=?"; params.append(fv)
        if q:
            sql += " AND (i.invoice_number LIKE ? OR c.name LIKE ?)"; params += [f"%{q}%"]*2
        sql += " ORDER BY i.id DESC"
        rows = conn.execute(sql, params).fetchall()

        cfg = {r["key"]:r["value"] for r in conn.execute("SELECT key,value FROM settings").fetchall()}
        total_inv  = conn.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
        total_paid = conn.execute("SELECT COALESCE(SUM(paid_amount),0) FROM invoices").fetchone()[0]
        total_due  = conn.execute("SELECT COALESCE(SUM(total_amount-paid_amount),0) FROM invoices").fetchone()[0]
        conn.close()

        curr = cfg.get("currency_symbol","Rs.")
        self._summary_lbl.config(
            text=f"     Total Invoices: {total_inv}     |"
                 f"     Collected: {curr} {total_paid:,.0f}     |"
                 f"     Outstanding: {curr} {total_due:,.0f}")

        self._tree.delete(*self._tree.get_children())
        for r in rows:
            self._tree.insert("","end", iid=str(r["id"]),
                              values=(r["invoice_number"], r["customer"] or "—", r["date"],
                                      f"{curr} {r['total_amount']:,.2f}",
                                      f"{curr} {r['paid_amount']:,.2f}",
                                      f"{curr} {r['balance']:,.2f}",
                                      r["status"].upper()),
                              tags=(r["status"],))

    def _sort(self, col):
        rows = [(self._tree.set(k, col), k) for k in self._tree.get_children("")]
        self._sort_rev = not self._sort_rev if self._sort_col == col else False
        self._sort_col = col
        rows.sort(reverse=self._sort_rev)
        for i,(_, k) in enumerate(rows): self._tree.move(k,"",i)

    def _sel_id(self):
        s = self._tree.focus(); return int(s) if s else None

    def _show_menu(self, e):
        r = self._tree.identify_row(e.y)
        if r: self._tree.focus(r); self._tree.selection_set(r); self._menu.post(e.x_root, e.y_root)

    def _new_invoice(self):
        InvoiceForm(self, on_saved=self._load)

    def _view_detail(self):
        i = self._sel_id()
        if i: InvoiceDetailWindow(self, i, on_edit=lambda: InvoiceForm(self, self._load, i))

    def _edit_invoice(self):
        i = self._sel_id()
        if i: InvoiceForm(self, on_saved=self._load, invoice_id=i)

    def _set_status(self, status):
        i = self._sel_id()
        if not i: return
        conn = get_connection()
        if status == "paid":
            t = conn.execute("SELECT total_amount FROM invoices WHERE id=?", (i,)).fetchone()["total_amount"]
            conn.execute("UPDATE invoices SET status=?,paid_amount=? WHERE id=?", (status,t,i))
        else:
            conn.execute("UPDATE invoices SET status=? WHERE id=?", (status,i))
        conn.commit(); conn.close(); self._load()

    def _delete_invoice(self):
        i = self._sel_id()
        if not i: return
        if messagebox.askyesno("Delete","Delete this invoice? This cannot be undone.", parent=self):
            conn = get_connection()
            conn.execute("DELETE FROM invoices WHERE id=?", (i,)); conn.commit(); conn.close()
            self._load()
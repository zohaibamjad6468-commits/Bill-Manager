import tkinter as tk
from tkinter import messagebox, ttk
import sys, os, datetime, calendar
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.db_connection import get_connection

# PDF libraries
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False

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
}

MONTHS = ["January","February","March","April","May","June",
          "July","August","September","October","November","December"]

def styled_btn(parent, text, command, color=None, fg="white", padx=14, pady=7):
    color = color or COLORS["accent"]
    return tk.Button(parent, text=text, command=command,
                     bg=color, fg=fg, font=("Segoe UI", 10, "bold"),
                     relief="flat", cursor="hand2", padx=padx, pady=pady,
                     activebackground=color, activeforeground=fg)


# =============================================================================
#  DATA FETCHER
# =============================================================================

def fetch_report_data(year, month_num):
    month_str = f"{year}-{month_num:02d}"
    conn = get_connection()
    cfg  = {r["key"]: r["value"] for r in
            conn.execute("SELECT key,value FROM settings").fetchall()}
    curr = cfg.get("currency_symbol", "Rs.")

    # ── Invoices ──────────────────────────────────────────────────────────────
    invoices = conn.execute("""
        SELECT i.invoice_number, c.name as customer, i.date,
               i.total_amount, i.paid_amount, i.status
        FROM invoices i LEFT JOIN customers c ON i.customer_id=c.id
        WHERE strftime('%Y-%m', i.date)=?
        ORDER BY i.date""", (month_str,)).fetchall()

    inv_total  = sum(r["total_amount"] for r in invoices)
    inv_paid   = sum(r["paid_amount"]  for r in invoices)
    inv_unpaid = inv_total - inv_paid
    inv_count  = len(invoices)
    paid_count = sum(1 for r in invoices if r["status"] == "paid")

    # ── Expenses ──────────────────────────────────────────────────────────────
    expenses = conn.execute("""
        SELECT date, category, description, amount
        FROM expenses WHERE strftime('%Y-%m', date)=?
        ORDER BY date""", (month_str,)).fetchall()

    total_expense = sum(r["amount"] for r in expenses)

    cat_totals = {}
    for r in expenses:
        cat_totals[r["category"]] = cat_totals.get(r["category"], 0) + r["amount"]

    # ── Staff & Salaries (hourly system) ──────────────────────────────────────
    staff_rows = conn.execute(
        "SELECT * FROM staff WHERE status='active' ORDER BY name").fetchall()

    staff_summary = []
    total_salary  = 0.0

    for s in staff_rows:
        hourly  = float(s["hourly_wage"]    or s["daily_wage"] or 0)
        std_hrs = float(s["standard_hours"] or 8)
        ot_rate = float(s["overtime_rate"]  or 1.5)

        att = conn.execute("""
            SELECT status,
                   SUM(hours_worked)   as total_hrs,
                   SUM(overtime_hours) as total_ot,
                   COUNT(*)            as days
            FROM attendance
            WHERE staff_id=? AND strftime('%Y-%m', date)=?
            GROUP BY status""", (s["id"], month_str)).fetchall()

        present = absent = halfday = 0
        reg_hrs = ot_hrs = 0.0

        for r in att:
            if r["status"] == "absent":
                absent  += int(r["days"])
            elif r["status"] == "half-day":
                halfday += int(r["days"])
                reg_hrs += float(r["total_hrs"] or 0)
                ot_hrs  += float(r["total_ot"]  or 0)
            else:
                present += int(r["days"])
                reg_hrs += float(r["total_hrs"] or 0)
                ot_hrs  += float(r["total_ot"]  or 0)

        salary = reg_hrs * hourly + ot_hrs * hourly * ot_rate
        total_salary += salary

        staff_summary.append({
            "name":    s["name"],
            "role":    s["role"] or "—",
            "wage":    hourly,
            "std_hrs": std_hrs,
            "reg_hrs": reg_hrs,
            "ot_hrs":  ot_hrs,
            "present": present,
            "absent":  absent,
            "halfday": halfday,
            "salary":  salary,
        })

    # ── Net figures ───────────────────────────────────────────────────────────
    net_profit = inv_paid - total_expense - total_salary

    conn.close()
    return {
        "cfg":           cfg,
        "curr":          curr,
        "month_str":     month_str,
        "month_name":    MONTHS[month_num - 1],
        "year":          year,
        "invoices":      [dict(r) for r in invoices],
        "inv_total":     inv_total,
        "inv_paid":      inv_paid,
        "inv_unpaid":    inv_unpaid,
        "inv_count":     inv_count,
        "paid_count":    paid_count,
        "expenses":      [dict(r) for r in expenses],
        "total_expense": total_expense,
        "cat_totals":    cat_totals,
        "staff_summary": staff_summary,
        "total_salary":  total_salary,
        "net_profit":    net_profit,
    }


# =============================================================================
#  PDF GENERATOR
# =============================================================================

def generate_pdf(data, filepath):
    if not REPORTLAB_OK:
        raise ImportError("reportlab not installed. Run: pip install reportlab")

    doc   = SimpleDocTemplate(filepath, pagesize=A4,
                              leftMargin=2*cm, rightMargin=2*cm,
                              topMargin=2*cm,  bottomMargin=2*cm)
    ss    = getSampleStyleSheet()
    curr  = data["curr"]
    story = []

    NAVY   = colors.HexColor("#1E2A3A")
    BLUE   = colors.HexColor("#2980B9")
    GREEN  = colors.HexColor("#27AE60")
    RED    = colors.HexColor("#E74C3C")
    ORANGE = colors.HexColor("#E67E22")
    LGREY  = colors.HexColor("#F4F6F8")
    MGREY  = colors.HexColor("#DDE1E7")

    def sty(name, **kw):
        base = ss["Normal"] if name not in ss.byName else ss[name]
        return ParagraphStyle(name + "_custom", parent=base, **kw)

    section_sty = sty("section_s", fontSize=13, textColor=NAVY,
                       spaceBefore=14, spaceAfter=6, fontName="Helvetica-Bold")
    bold_sty    = sty("bold_s",    fontSize=9,  fontName="Helvetica-Bold", textColor=NAVY)

    def section(title):
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(title, section_sty))
        story.append(HRFlowable(width="100%", thickness=1, color=BLUE, spaceAfter=6))

    def fmt(amount):
        return f"{curr} {amount:,.2f}"

    # ── Header ────────────────────────────────────────────────────────────────
    company = data["cfg"].get("company_name",   "Company")
    addr    = data["cfg"].get("company_address", "")
    phone   = data["cfg"].get("company_phone",   "")

    hdr_tbl = Table([[
        Paragraph(f"<b>{company}</b>",
                  sty("ch", fontSize=16, textColor=colors.white, fontName="Helvetica-Bold")),
        Paragraph(f"MONTHLY REPORT<br/>"
                  f"<font size=10>{data['month_name']} {data['year']}</font>",
                  sty("ct", fontSize=14, textColor=colors.white,
                      alignment=TA_RIGHT, fontName="Helvetica-Bold"))
    ]], colWidths=["60%", "40%"])
    hdr_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), NAVY),
        ("PADDING",    (0,0), (-1,-1), 14),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(hdr_tbl)
    if addr or phone:
        story.append(Paragraph(f"{addr}   {phone}",
                     sty("sub2", fontSize=9, textColor=BLUE, spaceBefore=4, spaceAfter=8)))
    story.append(Spacer(1, 0.2*cm))

    # ── Executive Summary cards ───────────────────────────────────────────────
    section("📊  Executive Summary")

    profit_color = GREEN if data["net_profit"] >= 0 else RED
    cards = [
        ["Total Sales",     fmt(data["inv_total"]),     BLUE],
        ["Amount Received", fmt(data["inv_paid"]),      GREEN],
        ["Total Expenses",  fmt(data["total_expense"]), RED],
        ["Staff Cost",      fmt(data["total_salary"]),  ORANGE],
        ["Net Profit/Loss", fmt(data["net_profit"]),    profit_color],
    ]
    combined = [[
        Paragraph(f"<b>{c[0]}</b><br/>{c[1]}",
                  sty(f"sc{i}", fontSize=9, textColor=colors.white,
                      alignment=TA_CENTER, fontName="Helvetica-Bold", leading=16))
        for i, c in enumerate(cards)
    ]]
    sum_tbl = Table(combined, colWidths=[3.2*cm]*5, rowHeights=[1.4*cm])
    cmds = [("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ("ALIGN", (0,0),(-1,-1),"CENTER"),
            ("PADDING",(0,0),(-1,-1),8)]
    for i, c in enumerate(cards):
        cmds.append(("BACKGROUND", (i,0),(i,0), c[2]))
    sum_tbl.setStyle(TableStyle(cmds))
    story.append(sum_tbl)
    story.append(Spacer(1, 0.4*cm))

    # ── Invoices ──────────────────────────────────────────────────────────────
    section(f"🧾  Sales & Invoices  ({data['inv_count']} invoices)")

    inv_rows = [[r["invoice_number"], r["customer"] or "—", r["date"],
                 fmt(r["total_amount"]), fmt(r["paid_amount"]), r["status"].upper()]
                for r in data["invoices"]] or [["—","No invoices this month","","","",""]]

    inv_tbl = Table([["Invoice #","Customer","Date","Total","Paid","Status"]] + inv_rows,
                    colWidths=[3*cm, 5*cm, 2.5*cm, 3*cm, 3*cm, 2*cm])
    inv_style = [
        ("BACKGROUND",    (0,0),  (-1,0),  NAVY),
        ("TEXTCOLOR",     (0,0),  (-1,0),  colors.white),
        ("FONTNAME",      (0,0),  (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),  (-1,-1), 8),
        ("ALIGN",         (3,0),  (-1,-1), "RIGHT"),
        ("ROWBACKGROUNDS",(0,1),  (-1,-1), [colors.white, LGREY]),
        ("GRID",          (0,0),  (-1,-1), 0.5, MGREY),
        ("PADDING",       (0,0),  (-1,-1), 5),
        ("TOPPADDING",    (0,0),  (-1,0),  8),
        ("BOTTOMPADDING", (0,0),  (-1,0),  8),
    ]
    for i, r in enumerate(data["invoices"]):
        sc = GREEN if r["status"]=="paid" else (ORANGE if r["status"]=="partial" else RED)
        inv_style += [("TEXTCOLOR",(5,i+1),(5,i+1),sc),
                      ("FONTNAME", (5,i+1),(5,i+1),"Helvetica-Bold")]
    inv_tbl.setStyle(TableStyle(inv_style))
    story.append(inv_tbl)

    itot = Table([
        ["","","Total Billed:",   fmt(data["inv_total"])],
        ["","","Total Received:", fmt(data["inv_paid"])],
        ["","","Outstanding:",    fmt(data["inv_unpaid"])],
    ], colWidths=[5*cm, 5*cm, 4*cm, 4.5*cm])
    itot.setStyle(TableStyle([
        ("ALIGN",    (2,0),(-1,-1),"RIGHT"),
        ("FONTNAME", (2,0),(2,-1), "Helvetica-Bold"),
        ("FONTNAME", (3,2),(3,2),  "Helvetica-Bold"),
        ("TEXTCOLOR",(3,2),(3,2),  RED),
        ("FONTSIZE", (0,0),(-1,-1),8),
        ("PADDING",  (0,0),(-1,-1),3),
    ]))
    story.append(Spacer(1, 0.2*cm))
    story.append(itot)

    # ── Expenses ──────────────────────────────────────────────────────────────
    section(f"💸  Expenses  ({len(data['expenses'])} entries)")

    exp_rows = [[r["date"], r["category"], r["description"] or "—", fmt(r["amount"])]
                for r in data["expenses"]] or [["—","No expenses this month","","—"]]

    exp_tbl = Table([["Date","Category","Description","Amount"]] + exp_rows,
                    colWidths=[2.5*cm, 3.5*cm, 7.5*cm, 3*cm])
    exp_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  ORANGE),
        ("TEXTCOLOR",     (0,0), (-1,0),  colors.white),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
        ("ALIGN",         (3,0), (3,-1),  "RIGHT"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, LGREY]),
        ("GRID",          (0,0), (-1,-1), 0.5, MGREY),
        ("PADDING",       (0,0), (-1,-1), 5),
        ("TOPPADDING",    (0,0), (-1,0),  8),
        ("BOTTOMPADDING", (0,0), (-1,0),  8),
    ]))
    story.append(exp_tbl)

    if data["cat_totals"]:
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph("Expense Breakdown by Category", bold_sty))
        story.append(Spacer(1, 0.2*cm))
        cat_rows = [[cat, fmt(amt),
                     f"{amt/data['total_expense']*100:.1f}%" if data["total_expense"] else "0%"]
                    for cat, amt in sorted(data["cat_totals"].items(),
                                           key=lambda x: x[1], reverse=True)]
        cat_rows.append(["TOTAL", fmt(data["total_expense"]), "100%"])
        cat_tbl = Table([["Category","Amount","Share"]] + cat_rows,
                        colWidths=[7*cm, 4*cm, 2.5*cm])
        cat_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0),  (-1,0),  ORANGE),
            ("TEXTCOLOR",  (0,0),  (-1,0),  colors.white),
            ("FONTNAME",   (0,0),  (-1,0),  "Helvetica-Bold"),
            ("FONTNAME",   (0,-1), (-1,-1), "Helvetica-Bold"),
            ("BACKGROUND", (0,-1), (-1,-1), LGREY),
            ("FONTSIZE",   (0,0),  (-1,-1), 8),
            ("ALIGN",      (1,0),  (-1,-1), "RIGHT"),
            ("GRID",       (0,0),  (-1,-1), 0.5, MGREY),
            ("PADDING",    (0,0),  (-1,-1), 5),
        ]))
        story.append(cat_tbl)

    # ── Staff Salaries (hourly system) ────────────────────────────────────────
    section(f"👷  Staff Salaries  ({len(data['staff_summary'])} active)")

    PURPLE = colors.HexColor("#8E44AD")

    sal_rows = [
        [s["name"], s["role"],
         fmt(s["wage"]) + "/hr",
         f"{s['reg_hrs']:.1f}",
         f"{s['ot_hrs']:.1f}",
         fmt(s["salary"])]
        for s in data["staff_summary"]
    ] or [["No active staff", "", "", "", "", ""]]
    sal_rows.append(["", "", "", "", "TOTAL", fmt(data["total_salary"])])

    sal_tbl = Table(
        [["Name", "Role", "Hourly Wage", "Reg Hrs", "OT Hrs", "Salary"]] + sal_rows,
        colWidths=[4.5*cm, 3*cm, 3*cm, 2*cm, 2*cm, 4*cm]
    )
    sal_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),  (-1,0),  PURPLE),
        ("TEXTCOLOR",     (0,0),  (-1,0),  colors.white),
        ("FONTNAME",      (0,0),  (-1,0),  "Helvetica-Bold"),
        ("FONTNAME",      (4,-1), (-1,-1), "Helvetica-Bold"),
        ("BACKGROUND",    (0,-1), (-1,-1), LGREY),
        ("FONTSIZE",      (0,0),  (-1,-1), 8),
        ("ALIGN",         (2,0),  (-1,-1), "RIGHT"),
        ("ROWBACKGROUNDS",(0,1),  (-2,-1), [colors.white, LGREY]),
        ("GRID",          (0,0),  (-1,-1), 0.5, MGREY),
        ("PADDING",       (0,0),  (-1,-1), 5),
        ("TOPPADDING",    (0,0),  (-1,0),  8),
        ("BOTTOMPADDING", (0,0),  (-1,0),  8),
    ]))
    story.append(sal_tbl)

    # ── P&L Summary ───────────────────────────────────────────────────────────
    section("📈  Profit & Loss Summary")

    pl_color = GREEN if data["net_profit"] >= 0 else RED
    pl_label = "NET PROFIT" if data["net_profit"] >= 0 else "NET LOSS"

    pl_tbl = Table([
        ["Total Revenue (Received)", fmt(data["inv_paid"])],
        ["Less: Operating Expenses", fmt(data["total_expense"])],
        ["Less: Staff Salaries",     fmt(data["total_salary"])],
        [pl_label,                   fmt(abs(data["net_profit"]))],
    ], colWidths=[10*cm, 5*cm])
    pl_tbl.setStyle(TableStyle([
        ("FONTSIZE",        (0,0), (-1,-1), 9),
        ("FONTNAME",        (0,3), (-1,3),  "Helvetica-Bold"),
        ("BACKGROUND",      (0,3), (-1,3),  pl_color),
        ("TEXTCOLOR",       (0,3), (-1,3),  colors.white),
        ("ALIGN",           (1,0), (1,-1),  "RIGHT"),
        ("GRID",            (0,0), (-1,-1), 0.5, MGREY),
        ("ROWBACKGROUNDS",  (0,0), (-1,2),  [colors.white, LGREY, colors.white]),
        ("PADDING",         (0,0), (-1,-1), 8),
        ("TOPPADDING",      (0,3), (-1,3),  10),
        ("BOTTOMPADDING",   (0,3), (-1,3),  10),
        ("LINEABOVE",       (0,3), (-1,3),  1.5, NAVY),
    ]))
    story.append(pl_tbl)

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MGREY))
    story.append(Paragraph(
        f"Report generated on {datetime.date.today().strftime('%d %B %Y')}  |  "
        f"{company}  |  Confidential",
        sty("footer_s", fontSize=7, textColor=colors.HexColor("#7F8C8D"),
            alignment=TA_CENTER, spaceBefore=6)))

    doc.build(story)


# =============================================================================
#  REPORTS PAGE
# =============================================================================

class ReportsPage(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORS["main_bg"], **kwargs)
        self._data = None
        self._build()

    def _build(self):
        bar = tk.Frame(self, bg=COLORS["white"],
                       highlightbackground=COLORS["border"], highlightthickness=1)
        bar.pack(fill="x")

        tk.Label(bar, text="Month:", bg=COLORS["white"],
                 fg=COLORS["text_dark"], font=("Segoe UI",10)
                 ).pack(side="left", padx=(16,4), pady=12)
        self._month_var = tk.StringVar(value=MONTHS[datetime.date.today().month - 1])
        ttk.Combobox(bar, textvariable=self._month_var, values=MONTHS,
                     font=("Segoe UI",10), width=12, state="readonly"
                     ).pack(side="left", pady=12)

        tk.Label(bar, text="Year:", bg=COLORS["white"],
                 fg=COLORS["text_dark"], font=("Segoe UI",10)
                 ).pack(side="left", padx=(12,4))
        years = [str(y) for y in range(2020, datetime.date.today().year + 3)]
        self._year_var = tk.StringVar(value=str(datetime.date.today().year))
        ttk.Combobox(bar, textvariable=self._year_var, values=years,
                     font=("Segoe UI",10), width=8, state="readonly"
                     ).pack(side="left", pady=12)

        styled_btn(bar, "  Load Report", self._load_report,
                   color=COLORS["accent"], padx=16, pady=7).pack(side="left", padx=12)
        styled_btn(bar, "  Export PDF",  self._export_pdf,
                   color=COLORS["danger"], padx=16, pady=7).pack(side="left", padx=4)

        self._status_lbl = tk.Label(bar, text="  Select a month and click Load Report",
                                    bg=COLORS["white"], fg=COLORS["text_muted"],
                                    font=("Segoe UI",9))
        self._status_lbl.pack(side="left", padx=12)

        canvas = tk.Canvas(self, bg=COLORS["main_bg"], highlightthickness=0)
        sb = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        self._preview = tk.Frame(canvas, bg=COLORS["main_bg"])
        win = canvas.create_window((0,0), window=self._preview, anchor="nw")
        self._preview.bind("<Configure>",
                           lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

    def _load_report(self):
        month_num  = MONTHS.index(self._month_var.get()) + 1
        year       = int(self._year_var.get())
        self._data = fetch_report_data(year, month_num)
        self._render_preview()
        self._status_lbl.config(
            text=f"  Showing: {self._month_var.get()} {year}",
            fg=COLORS["success"])

    def _render_preview(self):
        d    = self._data
        curr = d["curr"]

        for w in self._preview.winfo_children():
            w.destroy()

        def card(parent, label, value, color, bg):
            f = tk.Frame(parent, bg=bg,
                         highlightbackground=color, highlightthickness=1)
            f.pack(side="left", fill="both", expand=True, padx=(0,10))
            tk.Label(f, text=value, bg=bg, fg=color,
                     font=("Segoe UI",20,"bold")).pack(padx=14, pady=(14,2))
            tk.Label(f, text=label, bg=bg, fg=COLORS["text_muted"],
                     font=("Segoe UI",9)).pack(padx=14, pady=(0,14))

        def section_header(title, color=COLORS["accent"]):
            f = tk.Frame(self._preview, bg=color)
            f.pack(fill="x", padx=24, pady=(14,0))
            tk.Label(f, text=f"  {title}", bg=color, fg="white",
                     font=("Segoe UI",11,"bold")).pack(side="left", padx=4, pady=8)

        # ── Title bar ─────────────────────────────────────────────────────────
        title_f = tk.Frame(self._preview, bg=COLORS["text_dark"])
        title_f.pack(fill="x", padx=24, pady=(20,0))
        tk.Label(title_f,
                 text=f"  {d['cfg'].get('company_name','Company')}  —  Monthly Report",
                 bg=COLORS["text_dark"], fg="white",
                 font=("Segoe UI",15,"bold")).pack(side="left", padx=8, pady=14)
        tk.Label(title_f, text=f"{d['month_name']} {d['year']}  ",
                 bg=COLORS["text_dark"], fg="#95A5A6",
                 font=("Segoe UI",12)).pack(side="right", padx=8, pady=14)

        # ── Summary cards ─────────────────────────────────────────────────────
        cards_f = tk.Frame(self._preview, bg=COLORS["main_bg"])
        cards_f.pack(fill="x", padx=24, pady=14)
        profit_color = COLORS["success"] if d["net_profit"] >= 0 else COLORS["danger"]
        profit_bg    = "#EAFAF1"          if d["net_profit"] >= 0 else "#FDEDEC"
        card(cards_f, "Total Billed",    f"{curr} {d['inv_total']:,.0f}",     COLORS["accent"],  "#EBF5FB")
        card(cards_f, "Amount Received", f"{curr} {d['inv_paid']:,.0f}",      COLORS["success"], "#EAFAF1")
        card(cards_f, "Total Expenses",  f"{curr} {d['total_expense']:,.0f}", COLORS["danger"],  "#FDEDEC")
        card(cards_f, "Staff Cost",      f"{curr} {d['total_salary']:,.0f}",  COLORS["warning"], "#FEF9E7")
        card(cards_f, "Net Profit/Loss", f"{curr} {d['net_profit']:,.0f}",    profit_color,      profit_bg)

        # ── Invoices ──────────────────────────────────────────────────────────
        section_header(f"Invoices — {d['inv_count']} raised  |  {d['paid_count']} paid")
        inv_f = tk.Frame(self._preview, bg=COLORS["white"],
                         highlightbackground=COLORS["border"], highlightthickness=1)
        inv_f.pack(fill="x", padx=24, pady=(0,4))

        hdr = tk.Frame(inv_f, bg="#34495E"); hdr.pack(fill="x")
        for txt, w in [("Invoice #",120),("Customer",180),("Date",100),
                        ("Total",110),("Paid",110),("Status",90)]:
            tk.Label(hdr, text=txt, bg="#34495E", fg="white",
                     font=("Segoe UI",9,"bold"), width=w//8, anchor="w"
                     ).pack(side="left", padx=6, pady=6)

        if d["invoices"]:
            for i, r in enumerate(d["invoices"]):
                bg  = COLORS["row_alt"] if i%2 else COLORS["white"]
                row = tk.Frame(inv_f, bg=bg); row.pack(fill="x")
                sc  = {"paid": COLORS["success"], "unpaid": COLORS["danger"],
                        "partial": COLORS["accent"]}.get(r["status"], COLORS["text_muted"])
                for txt, w in [
                    (r["invoice_number"],15),(r["customer"] or "—",22),(r["date"],12),
                    (f"{curr} {r['total_amount']:,.0f}",13),
                    (f"{curr} {r['paid_amount']:,.0f}",13),
                ]:
                    tk.Label(row, text=txt, bg=bg, fg=COLORS["text_dark"],
                             font=("Segoe UI",9), width=w, anchor="w"
                             ).pack(side="left", padx=6, pady=5)
                tk.Label(row, text=r["status"].upper(), bg=bg, fg=sc,
                         font=("Segoe UI",9,"bold"), width=10, anchor="w"
                         ).pack(side="left", padx=6)
        else:
            tk.Label(inv_f, text="  No invoices for this period.",
                     bg=COLORS["white"], fg=COLORS["text_muted"],
                     font=("Segoe UI",10)).pack(anchor="w", padx=14, pady=12)

        # ── Expenses ──────────────────────────────────────────────────────────
        section_header(f"Expenses — {len(d['expenses'])} entries", color=COLORS["warning"])
        exp_f = tk.Frame(self._preview, bg=COLORS["white"],
                         highlightbackground=COLORS["border"], highlightthickness=1)
        exp_f.pack(fill="x", padx=24, pady=(0,4))

        hdr2 = tk.Frame(exp_f, bg="#34495E"); hdr2.pack(fill="x")
        for txt, w in [("Date",90),("Category",140),("Description",260),("Amount",110)]:
            tk.Label(hdr2, text=txt, bg="#34495E", fg="white",
                     font=("Segoe UI",9,"bold"), width=w//8, anchor="w"
                     ).pack(side="left", padx=6, pady=6)

        if d["expenses"]:
            for i, r in enumerate(d["expenses"]):
                bg  = COLORS["row_alt"] if i%2 else COLORS["white"]
                row = tk.Frame(exp_f, bg=bg); row.pack(fill="x")
                for txt, w in [(r["date"],11),(r["category"],17),
                               (r["description"] or "—",32),
                               (f"{curr} {r['amount']:,.0f}",13)]:
                    tk.Label(row, text=txt, bg=bg, fg=COLORS["text_dark"],
                             font=("Segoe UI",9), width=w, anchor="w"
                             ).pack(side="left", padx=6, pady=5)
        else:
            tk.Label(exp_f, text="  No expenses for this period.",
                     bg=COLORS["white"], fg=COLORS["text_muted"],
                     font=("Segoe UI",10)).pack(anchor="w", padx=14, pady=12)

        if d["cat_totals"]:
            cat_f = tk.Frame(self._preview, bg=COLORS["white"],
                             highlightbackground=COLORS["border"], highlightthickness=1)
            cat_f.pack(fill="x", padx=24, pady=(0,4))
            tk.Label(cat_f, text="  Category Breakdown", bg=COLORS["label_bg"],
                     fg=COLORS["text_dark"], font=("Segoe UI",10,"bold")
                     ).pack(fill="x", ipady=6)
            inner = tk.Frame(cat_f, bg=COLORS["white"])
            inner.pack(fill="x", padx=14, pady=8)
            for cat, amt in sorted(d["cat_totals"].items(), key=lambda x: x[1], reverse=True):
                pct = amt / d["total_expense"] * 100 if d["total_expense"] > 0 else 0
                r   = tk.Frame(inner, bg=COLORS["white"]); r.pack(fill="x", pady=3)
                tk.Label(r, text=cat, bg=COLORS["white"], fg=COLORS["text_dark"],
                         font=("Segoe UI",9), width=20, anchor="w").pack(side="left")
                tk.Label(r, text=f"{curr} {amt:,.0f}", bg=COLORS["white"],
                         fg=COLORS["danger"], font=("Segoe UI",9,"bold"),
                         width=14, anchor="e").pack(side="right")
                tk.Label(r, text=f"{pct:.1f}%", bg=COLORS["white"],
                         fg=COLORS["text_muted"], font=("Segoe UI",9),
                         width=8, anchor="e").pack(side="right")
                bar_bg = tk.Frame(inner, bg=COLORS["border"], height=4)
                bar_bg.pack(fill="x", pady=(0,2))
                tk.Frame(bar_bg, bg=COLORS["warning"], height=4
                         ).place(relwidth=pct/100, relheight=1)

        # ── Staff Salaries ─────────────────────────────────────────────────────
        section_header(f"Staff Salaries — {len(d['staff_summary'])} active",
                       color="#8E44AD")
        sal_f = tk.Frame(self._preview, bg=COLORS["white"],
                         highlightbackground=COLORS["border"], highlightthickness=1)
        sal_f.pack(fill="x", padx=24, pady=(0,4))

        hdr3 = tk.Frame(sal_f, bg="#34495E"); hdr3.pack(fill="x")
        for txt, w in [("Name",160),("Role",130),("Hourly Wage",110),
                        ("Reg Hrs",80),("OT Hrs",70),("Salary",120)]:
            tk.Label(hdr3, text=txt, bg="#34495E", fg="white",
                     font=("Segoe UI",9,"bold"), width=w//8, anchor="w"
                     ).pack(side="left", padx=6, pady=6)

        if d["staff_summary"]:
            for i, s in enumerate(d["staff_summary"]):
                bg  = COLORS["row_alt"] if i%2 else COLORS["white"]
                row = tk.Frame(sal_f, bg=bg); row.pack(fill="x")
                ot_color = COLORS["accent"] if s["ot_hrs"] > 0 else COLORS["text_dark"]
                for txt, w, clr in [
                    (s["name"],                          20, COLORS["text_dark"]),
                    (s["role"],                          16, COLORS["text_dark"]),
                    (f"{curr} {s['wage']:,.0f}/hr",      14, COLORS["text_dark"]),
                    (f"{s['reg_hrs']:.1f} hrs",          10, COLORS["success"]),
                    (f"{s['ot_hrs']:.1f} hrs",            9, ot_color),
                    (f"{curr} {s['salary']:,.0f}",       14, COLORS["text_dark"]),
                ]:
                    tk.Label(row, text=txt, bg=bg, fg=clr,
                             font=("Segoe UI",9), width=w, anchor="w"
                             ).pack(side="left", padx=6, pady=5)
        else:
            tk.Label(sal_f, text="  No active staff.",
                     bg=COLORS["white"], fg=COLORS["text_muted"],
                     font=("Segoe UI",10)).pack(anchor="w", padx=14, pady=12)

        tot_row = tk.Frame(sal_f, bg=COLORS["label_bg"]); tot_row.pack(fill="x")
        tk.Label(tot_row, text="Total Staff Cost:", bg=COLORS["label_bg"],
                 fg=COLORS["text_dark"], font=("Segoe UI",10,"bold")
                 ).pack(side="left", padx=14, pady=8)
        tk.Label(tot_row, text=f"{curr} {d['total_salary']:,.0f}",
                 bg=COLORS["label_bg"], fg="#8E44AD",
                 font=("Segoe UI",12,"bold")).pack(side="right", padx=14)

        # ── P&L Summary ───────────────────────────────────────────────────────
        section_header("Profit & Loss Summary", color=COLORS["text_dark"])
        pl_f = tk.Frame(self._preview, bg=COLORS["white"],
                        highlightbackground=COLORS["border"], highlightthickness=1)
        pl_f.pack(fill="x", padx=24, pady=(0,24))

        for label, amt, color in [
            ("Total Revenue (Received)",  d["inv_paid"],        COLORS["success"]),
            ("Less: Operating Expenses", -d["total_expense"],   COLORS["danger"]),
            ("Less: Staff Salaries",     -d["total_salary"],    COLORS["warning"]),
        ]:
            r = tk.Frame(pl_f, bg=COLORS["white"]); r.pack(fill="x", padx=20, pady=4)
            tk.Label(r, text=label, bg=COLORS["white"], fg=COLORS["text_dark"],
                     font=("Segoe UI",10)).pack(side="left")
            sign = "+" if amt >= 0 else "−"
            tk.Label(r, text=f"{sign} {curr} {abs(amt):,.0f}",
                     bg=COLORS["white"], fg=color,
                     font=("Segoe UI",10,"bold")).pack(side="right")

        tk.Frame(pl_f, bg=COLORS["border"], height=1).pack(fill="x", padx=20, pady=4)

        net_color = COLORS["success"] if d["net_profit"] >= 0 else COLORS["danger"]
        net_bg    = "#EAFAF1"          if d["net_profit"] >= 0 else "#FDEDEC"
        net_label = "NET PROFIT"       if d["net_profit"] >= 0 else "NET LOSS"
        net_f = tk.Frame(pl_f, bg=net_bg); net_f.pack(fill="x", padx=20, pady=(0,12))
        tk.Label(net_f, text=net_label, bg=net_bg, fg=net_color,
                 font=("Segoe UI",13,"bold")).pack(side="left", padx=14, pady=12)
        tk.Label(net_f, text=f"{curr} {abs(d['net_profit']):,.0f}",
                 bg=net_bg, fg=net_color,
                 font=("Segoe UI",18,"bold")).pack(side="right", padx=14)

    def _export_pdf(self):
        if not self._data:
            messagebox.showwarning("No Data",
                "Please click 'Load Report' first before exporting.", parent=self)
            return
        if not REPORTLAB_OK:
            messagebox.showerror("Missing Library",
                "reportlab is not installed.\n\nRun:\n\n    pip install reportlab\n\n"
                "Then restart the app.", parent=self)
            return

        from tkinter import filedialog
        d        = self._data
        filepath = filedialog.asksaveasfilename(
            title="Save Report PDF",
            initialfile=f"Report_{d['month_name']}_{d['year']}.pdf",
            defaultextension=".pdf",
            filetypes=[("PDF Files","*.pdf"),("All Files","*.*")]
        )
        if not filepath:
            return

        self._status_lbl.config(text="  Generating PDF...", fg=COLORS["warning"])
        self.update_idletasks()

        try:
            generate_pdf(d, filepath)
            self._status_lbl.config(text="  PDF exported successfully!", fg=COLORS["success"])
            if messagebox.askyesno("Success",
                    f"PDF saved to:\n{filepath}\n\nOpen the file now?", parent=self):
                if os.name == "nt":
                    os.startfile(filepath)
                else:
                    os.system(f'open "{filepath}"' if sys.platform == "darwin"
                              else f'xdg-open "{filepath}"')
        except Exception as ex:
            self._status_lbl.config(text="  Export failed.", fg=COLORS["danger"])
            messagebox.showerror("Export Failed",
                f"PDF could not be generated.\n\nError:\n{str(ex)}", parent=self)
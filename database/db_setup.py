import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_connection import get_connection

def setup_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, phone TEXT, address TEXT, email TEXT,
        created_at TEXT DEFAULT (date('now')))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, unit_price REAL NOT NULL DEFAULT 0,
        unit TEXT DEFAULT 'pcs', description TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT UNIQUE NOT NULL,
        customer_id INTEGER, date TEXT NOT NULL, due_date TEXT,
        total_amount REAL DEFAULT 0, paid_amount REAL DEFAULT 0,
        discount REAL DEFAULT 0, notes TEXT, status TEXT DEFAULT 'unpaid',
        FOREIGN KEY (customer_id) REFERENCES customers(id))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL, product_id INTEGER,
        description TEXT, quantity REAL NOT NULL DEFAULT 1,
        unit_price REAL NOT NULL DEFAULT 0, subtotal REAL NOT NULL DEFAULT 0,
        FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL, category TEXT NOT NULL,
        description TEXT, amount REAL NOT NULL DEFAULT 0)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS staff (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, role TEXT,
        daily_wage REAL DEFAULT 0,
        hourly_wage REAL DEFAULT 0,
        standard_hours REAL DEFAULT 8,
        overtime_rate REAL DEFAULT 1.5,
        phone TEXT, address TEXT, join_date TEXT,
        status TEXT DEFAULT 'active')''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        staff_id INTEGER NOT NULL, date TEXT NOT NULL,
        status TEXT DEFAULT 'present',
        hours_worked REAL DEFAULT 8,
        overtime_hours REAL DEFAULT 0,
        notes TEXT,
        FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE,
        UNIQUE(staff_id, date))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY, value TEXT)''')

    defaults = [
        ('company_name','Your Company Name'),('company_address','Company Address'),
        ('company_phone',''),('company_email',''),('company_website',''),
        ('invoice_prefix','INV'),('currency_symbol','Rs.'),('tax_rate','0'),
        ('invoice_footer','Thank you for your business!'),
        ('bank_name',''),('bank_account_title',''),('bank_account_no',''),
        ('bank_iban',''),('business_type',''),('fy_start','January'),
    ]
    for key, value in defaults:
        cursor.execute('INSERT OR IGNORE INTO settings (key,value) VALUES (?,?)', (key, value))

    # Migrate existing databases safely
    existing_staff_cols = [r[1] for r in cursor.execute("PRAGMA table_info(staff)").fetchall()]
    for col, defval in [
        ("hourly_wage",    "0"),
        ("standard_hours", "8"),
        ("overtime_rate",  "1.5"),
    ]:
        if col not in existing_staff_cols:
            cursor.execute(f"ALTER TABLE staff ADD COLUMN {col} REAL DEFAULT {defval}")

    existing_att_cols = [r[1] for r in cursor.execute("PRAGMA table_info(attendance)").fetchall()]
    for col, defval in [
        ("hours_worked",   "8"),
        ("overtime_hours", "0"),
    ]:
        if col not in existing_att_cols:
            cursor.execute(f"ALTER TABLE attendance ADD COLUMN {col} REAL DEFAULT {defval}")

    conn.commit()
    conn.close()
    print("Database ready.")

if __name__ == '__main__':
    setup_database()
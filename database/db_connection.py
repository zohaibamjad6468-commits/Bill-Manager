import sqlite3
import os
import sys

def get_db_path():
    """
    Always store the database next to the .exe (or main.py during development).
    This survives PyInstaller --onefile temp extraction because we look at
    sys.executable (the actual .exe path) not __file__ (the temp extract path).
    """
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller .exe — use the folder the .exe lives in
        base_dir = os.path.dirname(sys.executable)
    else:
        # Running as normal Python script — use the project root folder
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_dir, 'billing_data.db')

DB_PATH = get_db_path()

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
# BillManager

BillManager is a desktop billing and business management application built with Python and Tkinter.
It supports invoices, cash flow tracking, staff management, attendance, reports, and application settings.

## Features

- Dashboard with quick stats and recent invoices
- Invoice creation and tracking
- Cash flow / expense logging
- Staff management and attendance tracking
- PDF report generation
- Configurable company settings
- SQLite database setup automatically on first run

## Requirements

- Python 3.10+ (recommended)
- Windows is supported and the application is built with Tkinter GUI

Install required packages:

```bash
pip install -r requirements.txt
```

## Run the application

From the project root folder:

```bash
python main.py
```

The app will create and initialize the SQLite database automatically using `database/db_setup.py`.

## Project structure

- `main.py` - application entrypoint and UI layout
- `database/` - database connection and setup logic
- `modules/` - feature modules for invoices, cash flow, reports, staff, and settings
- `output/` - generated invoice files and report exports
- `requirements.txt` - Python dependencies

## Notes

- The first launch may take a moment while the SQLite database initializes.
- Update your company information in Settings before creating invoices and reports.
- If you need to reset the database, delete the SQLite file (for example, `billing_data.db`) and restart the app.

# CRM Desktop — Stage 04

The final stage of the CRM build. A native desktop application built with PySide6, backed by SQLite, packaged as a standalone executable.

## What's inside
crm-stage-04/
├── main.py PySide6 application (window, dialog, table)
├── database.py SQLite helpers
├── schema.sql The customers table
├── seed.py Sample data loader
├── requirements.txt PySide6 + pyinstaller
└── README.md This file

## Setup and run

### 1. Install dependencies

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

2. Seed the database

python seed.py
Expected output: Seeded 5 customers.

3. Run the app

python main.py
A native window opens with the CRM loaded. Add, edit, delete — all persisted to crm.db.

Packaging as a standalone executable
Once the app runs correctly with python main.py

pyinstaller --onefile --windowed --name "MAK CRM" main.py
This creates a dist/ folder with:

Windows: MAK CRM.exe (single file, no Python needed)

macOS: MAK CRM.app (application bundle)

Linux: MAK CRM (ELF binary)

The executable is self-contained. Ship it to anyone — they double-click and it runs.

Including the schema file
The app reads schema.sql at startup to create the database. When packaging, include it:

pyinstaller --onefile --windowed --name "MAK CRM" \
  --add-data "schema.sql:." \
  main.py
On Windows, use ; instead of ::

bash
pyinstaller --onefile --windowed --name "MAK CRM" ^
  --add-data "schema.sql;." ^
  main.py
Where the database lives
The app stores crm.db next to the executable (or next to main.py when running from source). This means:

Two copies of the app = two separate databases

Uninstalling the app = the database stays (unless deleted)

Backing up = copy crm.db

Troubleshooting
"No module named PySide6"
You didn't activate the venv, or pip install failed. Re-run:

bash
source venv/bin/activate
pip install -r requirements.txt
The app opens but shows no customers
Run python seed.py first. Or click "Add Customer" and add one manually.

PyInstaller produces a large file
PySide6 is ~100MB packaged. This is normal for Qt apps. The --onefile flag produces one large binary; without it, you get a folder with dependencies. Both work.

macOS: "App is damaged and can't be opened"
Unsigned apps trigger Gatekeeper. Right-click the app → Open → Open Anyway. Or sign the app with an Apple developer certificate.

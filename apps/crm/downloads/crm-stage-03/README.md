# CRM — Stage 03: Backend

The CRM with a real Python Flask backend and SQLite database.

## What's inside

crm-stage-03/
├── backend/
│ ├── app.py Flask application + REST API
│ ├── database.py SQLite connection management
│ ├── schema.sql Database schema (customers table)
│ ├── seed.py Sample data (run once)
│ └── requirements.txt Python dependencies
├── frontend/
│ └── index.html The CRM UI (fetches from the API)
└── README.md This file


## Setup (5 minutes)

### 1. Install Python dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

2. Seed the database
python seed.py

3. Start the server

python app.py

4. Open the app

 Open your browser to  Running on http://127.0.0.1:5000

You should see the CRM with 5 sample customers. Add, edit, delete — they all go through the Flask API and persist in SQLite.

How it works
The Flask server serves the frontend at /

The frontend calls the API at /api/customers

The API reads and writes to crm.db (SQLite)

Changes persist across server restarts (the database is a file)

The API
Method	Path	What it does
GET	/api/customers	List all customers
POST	/api/customers	Create a new customer
PUT	/api/customers/:id	Update a customer
DELETE	/api/customers/:id	Delete a customer
GET	/api/health	Health check

Testing the API directly
bash
# List customers
curl http://127.0.0.1:5000/api/customers

# Create a customer
curl -X POST http://127.0.0.1:5000/api/customers \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","status":"lead"}'

# Update a customer
curl -X PUT http://127.0.0.1:5000/api/customers/1 \
  -H "Content-Type: application/json" \
  -d '{"status":"active"}'

# Delete a customer
curl -X DELETE http://127.0.0.1:5000/api/customers/1

Stopping the server
Press Ctrl+C in the terminal.

Troubleshooting
"Address already in use"
Another process is using port 5000. Kill it, or change the port in app.py:

python
app.run(host='127.0.0.1', port=5001, debug=True)
Then update API_BASE in frontend/index.html to http://127.0.0.1:5001.

"Module not found: flask"
You didn't activate the virtual environment, or didn't install dependencies. Re-run:

bash
source venv/bin/activate
pip install -r requirements.txt
The frontend shows "Could not load customers"
The backend isn't running. Start it with python app.py.

CORS error in browser console
flask-cors handles this automatically for http://127.0.0.1:5000. If you're serving the frontend from a different port, add that origin to the CORS config in app.py

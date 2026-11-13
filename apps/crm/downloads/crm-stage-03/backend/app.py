"""
CRM Backend — Stage 03
Flask + SQLite REST API for the CRM customer list.
"""
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from database import get_db, init_db, close_db
import os

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# Register database cleanup
app.teardown_appcontext(close_db)


# ─────────────────────────────────────────────
# Frontend serving
# ─────────────────────────────────────────────

@app.route('/')
def index():
    """Serve the CRM frontend."""
    return send_from_directory(app.static_folder, 'index.html')


# ─────────────────────────────────────────────
# API: Customers
# ─────────────────────────────────────────────

@app.route('/api/customers', methods=['GET'])
def list_customers():
    """GET /api/customers — return all customers, newest first."""
    db = get_db()
    rows = db.execute(
        'SELECT id, name, email, phone, company, status, notes, '
        'created_at AS createdAt, updated_at AS updatedAt '
        'FROM customers ORDER BY created_at DESC'
    ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.route('/api/customers', methods=['POST'])
def create_customer():
    """POST /api/customers — create a new customer."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()

    if not name:
        return jsonify({'error': 'Name is required'}), 400
    if not email:
        return jsonify({'error': 'Email is required'}), 400

    db = get_db()
    cursor = db.execute(
        'INSERT INTO customers (name, email, phone, company, status, notes) '
        'VALUES (?, ?, ?, ?, ?, ?)',
        (
            name,
            email,
            data.get('phone') or '',
            data.get('company') or '',
            data.get('status') or 'lead',
            data.get('notes') or '',
        )
    )
    db.commit()

    row = db.execute(
        'SELECT id, name, email, phone, company, status, notes, '
        'created_at AS createdAt, updated_at AS updatedAt '
        'FROM customers WHERE id = ?',
        (cursor.lastrowid,)
    ).fetchone()

    return jsonify(dict(row)), 201


@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """PUT /api/customers/:id — update an existing customer."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    db = get_db()
    existing = db.execute(
        'SELECT * FROM customers WHERE id = ?', (customer_id,)
    ).fetchone()

    if not existing:
        return jsonify({'error': 'Customer not found'}), 404

    name = (data.get('name') or existing['name']).strip()
    email = (data.get('email') or existing['email']).strip()

    if not name:
        return jsonify({'error': 'Name is required'}), 400
    if not email:
        return jsonify({'error': 'Email is required'}), 400

    db.execute(
        'UPDATE customers SET name = ?, email = ?, phone = ?, company = ?, '
        'status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
        (
            name,
            email,
            data.get('phone') or '',
            data.get('company') or '',
            data.get('status') or existing['status'],
            data.get('notes') or '',
            customer_id,
        )
    )
    db.commit()

    row = db.execute(
        'SELECT id, name, email, phone, company, status, notes, '
        'created_at AS createdAt, updated_at AS updatedAt '
        'FROM customers WHERE id = ?',
        (customer_id,)
    ).fetchone()

    return jsonify(dict(row))


@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """DELETE /api/customers/:id — remove a customer."""
    db = get_db()
    existing = db.execute(
        'SELECT * FROM customers WHERE id = ?', (customer_id,)
    ).fetchone()

    if not existing:
        return jsonify({'error': 'Customer not found'}), 404

    db.execute('DELETE FROM customers WHERE id = ?', (customer_id,))
    db.commit()

    return jsonify({'deleted': customer_id}), 200


# ─────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'service': 'crm-backend'})


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(host='127.0.0.1', port=5000, debug=True)

"""
Database layer for the CRM desktop app.
Uses SQLite for local persistence. No server required.
"""
import sqlite3
import os
import sys

# Store the database next to the executable / script
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(APP_DIR, 'crm.db')


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the customers table if it doesn't exist."""
    schema_path = os.path.join(APP_DIR, 'schema.sql')
    with _conn() as conn:
        with open(schema_path) as f:
            conn.executescript(f.read())


def get_all_customers():
    """Return all customers, newest first."""
    with _conn() as conn:
        rows = conn.execute(
            'SELECT id, name, email, phone, company, status, notes, '
            'created_at AS createdAt, updated_at AS updatedAt '
            'FROM customers ORDER BY created_at DESC'
        ).fetchall()
        return [dict(r) for r in rows]


def get_customer(customer_id):
    """Return a single customer, or None."""
    with _conn() as conn:
        row = conn.execute(
            'SELECT id, name, email, phone, company, status, notes, '
            'created_at AS createdAt, updated_at AS updatedAt '
            'FROM customers WHERE id = ?',
            (customer_id,)
        ).fetchone()
        return dict(row) if row else None


def insert_customer(data):
    """Insert a new customer, return the new id."""
    with _conn() as conn:
        cursor = conn.execute(
            'INSERT INTO customers (name, email, phone, company, status, notes) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            (
                data.get('name', ''),
                data.get('email', ''),
                data.get('phone', ''),
                data.get('company', ''),
                data.get('status', 'lead'),
                data.get('notes', ''),
            )
        )
        conn.commit()
        return cursor.lastrowid


def update_customer(customer_id, data):
    """Update an existing customer."""
    with _conn() as conn:
        conn.execute(
            'UPDATE customers SET name = ?, email = ?, phone = ?, company = ?, '
            'status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (
                data.get('name', ''),
                data.get('email', ''),
                data.get('phone', ''),
                data.get('company', ''),
                data.get('status', 'lead'),
                data.get('notes', ''),
                customer_id,
            )
        )
        conn.commit()


def delete_customer(customer_id):
    """Delete a customer by id."""
    with _conn() as conn:
        conn.execute('DELETE FROM customers WHERE id = ?', (customer_id,))
        conn.commit()


def get_counts():
    """Return counts by status for the KPI cards."""
    with _conn() as conn:
        rows = conn.execute(
            'SELECT status, COUNT(*) AS count FROM customers GROUP BY status'
        ).fetchall()
    counts = {"total": 0, "active": 0, "lead": 0, "inactive": 0}
    for row in rows:
        counts[row["status"]] = row["count"]
        counts["total"] += row["count"]
    return counts

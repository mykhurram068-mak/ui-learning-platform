"""
Seed the database with sample customers.
Run once: python seed.py
"""
from database import get_db, init_db
from flask import Flask
import sqlite3, os

SAMPLE_CUSTOMERS = [
    ('Alice Rahman', 'alice@example.com', '+92 300 1234567', 'Acme Corp', 'active', 'Met at the 2026 conference.'),
    ('Bob Chen', 'bob@northwind.io', '+1 555 0100', 'Northwind', 'lead', 'Requested a demo.'),
    ('Charlie Diaz', 'charlie@globex.com', '+1 555 0142', 'Globex', 'active', ''),
    ('Diana Okonkwo', 'diana@initech.co', '', 'Initech', 'inactive', 'Not responding.'),
    ('Evan Petrov', 'evan@umbrella.dev', '+1 555 0177', 'Umbrella Co', 'lead', 'Warm lead from LinkedIn.'),
]


def seed():
    init_db()
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'crm.db'))
    existing = db.execute('SELECT COUNT(*) FROM customers').fetchone()[0]
    if existing > 0:
        print(f'Database already has {existing} customers. Skipping seed.')
        db.close()
        return

    for row in SAMPLE_CUSTOMERS:
        db.execute(
            'INSERT INTO customers (name, email, phone, company, status, notes) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            row
        )
    db.commit()
    db.close()
    print(f'Seeded {len(SAMPLE_CUSTOMERS)} customers.')


if __name__ == '__main__':
    seed()

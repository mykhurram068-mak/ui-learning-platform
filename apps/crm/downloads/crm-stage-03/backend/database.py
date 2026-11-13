"""
Database layer — SQLite connection management.
"""
import sqlite3
from flask import g
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'crm.db')


def get_db():
    """Get a database connection for the current request."""
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(e=None):
    """Close the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Initialize the database schema (idempotent)."""
    db = sqlite3.connect(DB_PATH)
    with open(os.path.join(os.path.dirname(__file__), 'schema.sql')) as f:
        db.executescript(f.read())
    db.commit()
    db.close()

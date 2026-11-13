"""
Tiny helper module. Keeps schema loading and connection setup in one place.
"""

import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "inventory.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Drop and recreate the schema. Destructive — for development only."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = f.read()
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(schema)
    conn.commit()
    conn.close()
    print(f"Initialised {DB_PATH}")

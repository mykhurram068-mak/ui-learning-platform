"""
Creates inventory.db, applies schema.sql, and seeds sample data.
Run once: python seed.py
"""

from datetime import datetime, timezone
from database import init_db, connect

def now():
    return datetime.now(timezone.utc).isoformat()

def seed():
    init_db()
    conn = connect()

    suppliers = [
        ("Acme Peripherals",   "orders@acme-peripherals.example"),
        ("Northwind Cables",   "sales@northwind.example"),
        ("BrightDesk Supply",  "hello@brightdesk.example"),
    ]
    for name, email in suppliers:
        conn.execute(
            "INSERT INTO suppliers (name, email, created_at) VALUES (?, ?, ?)",
            (name, email, now()),
        )
    conn.commit()

    # Fetch supplier ids by name
    sid = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM suppliers")}

    products = [
        # sku, name, category, price, cost, qty, reorder, supplier
        ("SKU-001", "Wireless Mouse",       "Electronics", 29.99, 15.50, 42,  10, sid["Acme Peripherals"]),
        ("SKU-002", "Mechanical Keyboard",  "Electronics", 89.00, 45.00,  8,  10, sid["Acme Peripherals"]),
        ("SKU-003", "USB-C Cable (2m)",     "Accessories", 12.50,  4.20, 156, 20, sid["Northwind Cables"]),
        ("SKU-004", "Monitor Stand",        "Accessories", 45.00, 22.00,  0,   5, sid["BrightDesk Supply"]),
        ("SKU-005", "Webcam HD 1080p",      "Electronics", 79.99, 38.00, 15,   8, sid["Acme Peripherals"]),
        ("SKU-006", "Desk Lamp LED",        "Accessories", 34.00, 14.00,  3,   5, sid["BrightDesk Supply"]),
    ]
    for sku, name, cat, price, cost, qty, reorder, supplier_id in products:
        conn.execute(
            """INSERT INTO products
               (sku, name, category, price, cost, quantity, reorder_level,
                supplier_id, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sku, name, cat, price, cost, qty, reorder, supplier_id, now(), now()),
        )

    conn.commit()
    n_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    n_suppliers = conn.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0]
    conn.close()
    print(f"Seeded {n_suppliers} suppliers and {n_products} products.")

if __name__ == "__main__":
    seed()

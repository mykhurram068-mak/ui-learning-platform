"""
Creates or upgrades inventory.db and seeds sample POS data.

Run once for a fresh install: creates everything.
Run again on an existing Stage 03 database: applies the Stage 04
migrations (adds refund_of_sale_id, archived_at) without dropping
any data.

Migration strategy:
  - If sales table doesn't have refund_of_sale_id → ALTER TABLE add it.
  - If products table doesn't have archived_at     → ALTER TABLE add it.
  - Only seed sample sales if the sales table is empty.

This is the first real migration in the POS build. Stage 03
dropped and recreated; Stage 04 upgrades in place. Same pattern
you'd use in production, just smaller.
"""

import sqlite3
import os
from datetime import datetime, timezone, timedelta

from database import DB_PATH, connect, init_pos_tables


def now():
    return datetime.now(timezone.utc).isoformat()


def days_ago(n):
    return (datetime.now(timezone.utc) - timedelta(days=n)).isoformat()


def column_exists(conn, table, column):
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    return column in cols


def migrate(conn):
    """Apply Stage 04 migrations to an existing database."""
    applied = []

    if not column_exists(conn, "sales", "refund_of_sale_id"):
        conn.execute("ALTER TABLE sales ADD COLUMN refund_of_sale_id INTEGER")
        applied.append("sales.refund_of_sale_id")

    if not column_exists(conn, "products", "archived_at"):
        conn.execute("ALTER TABLE products ADD COLUMN archived_at TEXT")
        applied.append("products.archived_at")

    if applied:
        conn.commit()
        print("Migrations applied: " + ", ".join(applied))
    else:
        print("Schema is up to date — no migrations needed.")


def seed_products_if_empty(conn):
    count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count > 0:
        print(f"products already has {count} rows — leaving inventory data untouched.")
        return

    products = [
        ("SKU-001", "Wireless Mouse",       "Electronics", 29.99, 15.50, 42,  10),
        ("SKU-002", "Mechanical Keyboard",  "Electronics", 89.00, 45.00,  8,  10),
        ("SKU-003", "USB-C Cable (2m)",     "Accessories", 12.50,  4.20, 156, 20),
        ("SKU-004", "Monitor Stand",        "Accessories", 45.00, 22.00,  0,   5),
        ("SKU-005", "Webcam HD 1080p",      "Electronics", 79.99, 38.00, 15,   8),
        ("SKU-006", "Desk Lamp LED",        "Accessories", 34.00, 14.00,  3,   5),
        ("SKU-007", "HDMI Cable (1m)",      "Cables",       8.99,  2.50, 88,  15),
        ("SKU-008", "USB Hub 4-Port",       "Accessories", 22.50, 10.00, 27,  10),
    ]
    for sku, name, cat, price, cost, qty, reorder in products:
        conn.execute(
            """INSERT INTO products
               (sku, name, category, price, cost, quantity, reorder_level,
                supplier_id, archived_at, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?)""",
            (sku, name, cat, price, cost, qty, reorder, now(), now()),
        )
    conn.commit()
    print(f"Seeded {len(products)} products.")


def seed_sales_if_empty(conn):
    count = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    if count > 0:
        print(f"sales already has {count} rows — leaving sales alone.")
        return

    pid = {r["sku"]: r["id"] for r in conn.execute("SELECT id, sku FROM products").fetchall()}
    if not pid:
        print("No products — skipping sample sales.")
        return

    samples = [
        # (days_ago, cashier, [(sku, qty)...], payment_method, tendered)
        (3, "Alex Rivera", [("SKU-001", 1), ("SKU-003", 2)],  "cash", 60.00),
        (2, "Alex Rivera", [("SKU-002", 1)],                   "card", 0),
        (2, "Sam Patel",   [("SKU-007", 3), ("SKU-008", 1)],  "cash", 60.00),
        (1, "Alex Rivera", [("SKU-005", 1), ("SKU-001", 2)],  "card", 0),
        (0, "Sam Patel",   [("SKU-003", 5), ("SKU-007", 2)],  "cash", 100.00),
    ]
    tax_rate = 8.5

    for days, cashier, items, method, tendered in samples:
        resolved = []
        subtotal = 0.0
        for sku, qty in items:
            p = conn.execute(
                "SELECT id, name, price FROM products WHERE sku = ?", (sku,)
            ).fetchone()
            if not p:
                continue
            lt = round(p["price"] * qty, 2)
            subtotal += lt
            resolved.append({
                "product_id": p["id"], "name": p["name"], "qty": qty,
                "unit_price": p["price"], "line_total": lt,
            })

        if not resolved:
            continue

        subtotal = round(subtotal, 2)
        tax_total = round(subtotal * tax_rate / 100, 2)
        grand = round(subtotal + tax_total, 2)
        change = round(max(0, tendered - grand), 2) if method == "cash" else 0

        cur = conn.execute(
            """INSERT INTO sales
               (cashier, subtotal, tax_rate, tax_total, grand_total,
                status, refund_of_sale_id, created_at, paid_at)
               VALUES (?, ?, ?, ?, ?, 'paid', NULL, ?, ?)""",
            (cashier, subtotal, tax_rate, tax_total, grand,
             days_ago(days), days_ago(days)),
        )
        sale_id = cur.lastrowid

        for r in resolved:
            conn.execute(
                """INSERT INTO sale_lines
                   (sale_id, product_id, product_name, qty,
                    unit_price, line_total, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (sale_id, r["product_id"], r["name"], r["qty"],
                 r["unit_price"], r["line_total"], days_ago(days)),
            )
            conn.execute(
                """INSERT INTO stock_movements
                   (product_id, delta, reason, note, created_at)
                   VALUES (?, ?, 'sold', ?, ?)""",
                (r["product_id"], -r["qty"], f"POS sale #{sale_id}", days_ago(days)),
            )
            conn.execute(
                "UPDATE products SET quantity = quantity - ? WHERE id = ?",
                (r["qty"], r["product_id"]),
            )

        conn.execute(
            """INSERT INTO payments
               (sale_id, method, amount, tendered, change, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sale_id, method, grand,
             tendered if method == "cash" else grand,
             change, days_ago(days)),
        )

    conn.commit()
    print(f"Seeded {len(samples)} sales.")


def seed_extras(conn):
    """Seed one archived product and one held sale, so the
    Stage 04 UI has something to show in both features."""
    # Archived product — one that's been sold (so RESTRICT applies)
    archived_sku = "SKU-009"
    existing = conn.execute(
        "SELECT id FROM products WHERE sku = ?", (archived_sku,)
    ).fetchone()
    if not existing:
        conn.execute(
            """INSERT INTO products
               (sku, name, category, price, cost, quantity, reorder_level,
                supplier_id, archived_at, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, 0, 5, NULL, ?, ?, ?)""",
            (archived_sku, "Discontinued Webcam (Legacy)", "Electronics",
             59.99, 30.00, days_ago(30), days_ago(60), days_ago(30)),
        )
        conn.commit()
        print("Seeded 1 archived product (SKU-009).")

    # Held sale — a cart that was parked for later
    held = conn.execute(
        "SELECT id FROM sales WHERE status = 'held' LIMIT 1"
    ).fetchone()
    if not held:
        # Find a product with stock
        p = conn.execute(
            "SELECT id, name, price FROM products WHERE quantity > 0 AND archived_at IS NULL LIMIT 1"
        ).fetchone()
        if p:
            subtotal = round(p["price"] * 2, 2)
            tax_total = round(subtotal * 8.5 / 100, 2)
            grand = round(subtotal + tax_total, 2)
            cur = conn.execute(
                """INSERT INTO sales
                   (cashier, subtotal, tax_rate, tax_total, grand_total,
                    status, refund_of_sale_id, created_at, paid_at)
                   VALUES ('Alex Rivera', ?, 8.5, ?, ?, 'held', NULL, ?, NULL)""",
                (subtotal, tax_total, grand, days_ago(0)),
            )
            sale_id = cur.lastrowid
            conn.execute(
                """INSERT INTO sale_lines
                   (sale_id, product_id, product_name, qty,
                    unit_price, line_total, created_at)
                   VALUES (?, ?, ?, 2, ?, ?, ?)""",
                (sale_id, p["id"], p["name"], p["price"], subtotal, days_ago(0)),
            )
            conn.commit()
            print(f"Seeded 1 held sale (#{sale_id}).")


def main():
    print(f"Database: {DB_PATH}")
    fresh = not os.path.exists(DB_PATH) or not os.path.getsize(DB_PATH)
    init_pos_tables()
    conn = connect()
    if not fresh:
        migrate(conn)
    seed_products_if_empty(conn)
    seed_sales_if_empty(conn)
    seed_extras(conn)
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()

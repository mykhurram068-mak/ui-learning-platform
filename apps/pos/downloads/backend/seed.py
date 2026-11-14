"""
Creates inventory.db (if needed) and seeds sample POS data.

If inventory.db already exists from the Inventory Stage 04 build,
its products and stock_movements are left untouched. Only the
three POS tables (sales, sale_lines, payments) are recreated.

Run once: python seed.py
"""

import sqlite3
import os
from datetime import datetime, timezone, timedelta

from database import DB_PATH, connect, init_pos_tables


def now():
    return datetime.now(timezone.utc).isoformat()


def days_ago(n):
    return (datetime.now(timezone.utc) - timedelta(days=n)).isoformat()


def seed_products_if_empty(conn):
    """If products is empty, insert the 8 sample products from Stage 02.
    If it already has products (from the inventory build), leave them alone."""
    count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count > 0:
        print(f"products already has {count} rows — leaving inventory data untouched.")
        return

    products = [
        # sku, name, category, price, cost, qty, reorder
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
                supplier_id, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)""",
            (sku, name, cat, price, cost, qty, reorder, now(), now()),
        )
    conn.commit()
    print(f"Seeded {len(products)} products.")


def seed_sales(conn):
    """Insert a few sample sales for the history/report UI to display.
    These reference products by id, so we look them up by sku."""
    pid = {
        r["sku"]: r["id"]
        for r in conn.execute("SELECT id, sku FROM products").fetchall()
    }
    if not pid:
        print("No products — skipping sample sales.")
        return

    # Each sale is (days_ago, cashier, [(sku, qty), ...], payment)
    # payment: (method, tendered)  — tendered used only for cash
    samples = [
        (3, "Alex Rivera", [("SKU-001", 1), ("SKU-003", 2)],          ("cash", 60.00)),
        (2, "Alex Rivera", [("SKU-002", 1)],                           ("card", 0)),
        (2, "Sam Patel",   [("SKU-007", 3), ("SKU-008", 1)],          ("cash", 60.00)),
        (1, "Alex Rivera", [("SKU-005", 1), ("SKU-001", 2)],          ("card", 0)),
        (0, "Sam Patel",   [("SKU-003", 5), ("SKU-007", 2)],          ("cash", 100.00)),
    ]

    tax_rate = 8.5

    for days, cashier, items, payment in samples:
        subtotal = 0.0
        resolved = []
        for sku, qty in items:
            product = conn.execute(
                "SELECT id, name, price FROM products WHERE sku = ?", (sku,)
            ).fetchone()
            if not product:
                continue
            line_total = round(product["price"] * qty, 2)
            subtotal += line_total
            resolved.append({
                "product_id": product["id"],
                "name": product["name"],
                "qty": qty,
                "unit_price": product["price"],
                "line_total": line_total,
            })

        if not resolved:
            continue

        subtotal = round(subtotal, 2)
        tax_total = round(subtotal * tax_rate / 100, 2)
        grand_total = round(subtotal + tax_total, 2)

        cur = conn.execute(
            """INSERT INTO sales
               (cashier, subtotal, tax_rate, tax_total, grand_total,
                status, created_at, paid_at)
               VALUES (?, ?, ?, ?, ?, 'paid', ?, ?)""",
            (cashier, subtotal, tax_rate, tax_total, grand_total,
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
            # Stock movement — 'sold' with negative delta
            conn.execute(
                """INSERT INTO stock_movements
                   (product_id, delta, reason, note, created_at)
                   VALUES (?, ?, 'sold', ?, ?)""",
                (r["product_id"], -r["qty"], f"POS sale #{sale_id}", days_ago(days)),
            )
            # Update cached quantity
            conn.execute(
                "UPDATE products SET quantity = quantity - ? WHERE id = ?",
                (r["qty"], r["product_id"]),
            )

        method, tendered = payment
        change = round(max(0, tendered - grand_total), 2) if method == "cash" else 0
        conn.execute(
            """INSERT INTO payments
               (sale_id, method, amount, tendered, change, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sale_id, method, grand_total,
             tendered if method == "cash" else grand_total,
             change, days_ago(days)),
        )

    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    print(f"Seeded {n} sales.")


def main():
    print(f"Database: {DB_PATH}")
    init_pos_tables()
    conn = connect()
    seed_products_if_empty(conn)
    seed_sales(conn)
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()

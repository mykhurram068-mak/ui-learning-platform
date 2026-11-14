"""
POS API — Stage 03
Flask + SQLite backend. Three POS tables (sales, sale_lines, payments).
Reads products from the shared inventory database.
Writes stock_movements rows on every sale.

The atomic checkout at POST /api/sales is the heart of this stage:
insert sale, insert lines, insert payment, write stock movements,
decrement product quantities — all in one transaction. If any step
fails, none of it commits.

Run:
    pip install -r requirements.txt
    python seed.py
    python app.py       → http://localhost:5000
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "inventory.db")

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)


# ─────────────────────────────────────────────
# DB helpers
# ─────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def row_to_dict(row):
    return {k: row[k] for k in row.keys()} if row else None


def rows_to_list(rows):
    return [row_to_dict(r) for r in rows]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def round_money(n):
    return round(n + 1e-9, 2)   # +epsilon to avoid 8.565 → 8.56 in binary float


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "pos-stage-03.html")


# ─────────────────────────────────────────────
# CATALOG — reads from the shared inventory database
# ─────────────────────────────────────────────
@app.route("/api/products", methods=["GET"])
def list_products():
    """
    The POS catalog. Returns products with stock > 0, or all if ?all=1.
    This is intentionally the same shape as Inventory Stage 03's
    GET /api/products — one catalog, two consumers.
    """
    include_empty = request.args.get("all") == "1"

    where = "" if include_empty else "WHERE quantity > 0"
    with get_db() as conn:
        rows = conn.execute(
            f"""SELECT id, sku, name, category, price, quantity AS stock
                FROM products
                {where}
                ORDER BY category, name"""
        ).fetchall()

    return jsonify(rows_to_list(rows))


@app.route("/api/categories", methods=["GET"])
def list_categories():
    with get_db() as conn:
        rows = conn.execute(
            """SELECT DISTINCT category FROM products
               WHERE quantity > 0 AND category IS NOT NULL
               ORDER BY category"""
        ).fetchall()
    return jsonify([r["category"] for r in rows])


# ─────────────────────────────────────────────
# SALES — the atomic checkout
# ─────────────────────────────────────────────
@app.route("/api/sales", methods=["POST"])
def create_sale():
    """
    The atomic checkout. Body:
      {
        "cashier": "Alex Rivera",
        "taxRate": 8.5,
        "lines": [{"productId": 1, "qty": 2}, ...],
        "payment": {"method": "cash", "tendered": 100.00}
      }

    Steps inside ONE transaction:
      1. Validate every line (product exists, stock sufficient)
      2. Compute subtotal, tax, grand total server-side
      3. Insert `sales` row
      4. Insert `sale_lines` rows (with price snapshot)
      5. Insert `payments` row
      6. For each line: INSERT stock_movements + UPDATE products.quantity
      7. COMMIT

    Any failure rolls back every write. The database never holds
    a half-completed sale.
    """
    data = request.get_json(silent=True) or {}

    cashier = (data.get("cashier") or "Alex Rivera").strip()
    tax_rate = float(data.get("taxRate", 8.5))
    lines = data.get("lines") or []
    payment = data.get("payment") or {}

    if not lines:
        return jsonify({"error": "Cart is empty."}), 400
    if tax_rate < 0:
        return jsonify({"error": "Tax rate cannot be negative."}), 400

    method = (payment.get("method") or "cash").lower()
    if method not in ("cash", "card", "other"):
        return jsonify({"error": "Invalid payment method."}), 400

    # BEGIN TRANSACTION. Every write below is inside this block.
    # If any exception fires, sqlite3 rolls back and re-raises.
    with get_db() as conn:
        # 1. Validate lines + build the price snapshot
        resolved_lines = []
        for raw in lines:
            try:
                pid = int(raw["productId"])
                qty = int(raw["qty"])
            except (KeyError, TypeError, ValueError):
                return jsonify({"error": "Invalid line item."}), 400
            if qty <= 0:
                return jsonify({"error": "Quantity must be positive."}), 400

            product = conn.execute(
                "SELECT id, name, price, quantity FROM products WHERE id = ?",
                (pid,),
            ).fetchone()

            if not product:
                return jsonify({"error": f"Product {pid} not found."}), 404
            if product["quantity"] < qty:
                return jsonify({
                    "error": f'Only {product["quantity"]} of "{product["name"]}" '
                             f'in stock (tried to sell {qty}).'
                }), 409

            resolved_lines.append({
                "product_id": product["id"],
                "product_name": product["name"],
                "qty": qty,
                "unit_price": product["price"],
                "line_total": round_money(product["price"] * qty),
            })

        # 2. Compute totals SERVER-SIDE. Never trust the client's math.
        subtotal = round_money(sum(r["line_total"] for r in resolved_lines))
        tax_total = round_money(subtotal * tax_rate / 100)
        grand_total = round_money(subtotal + tax_total)

        # 3. Payment guard — cash must cover the total
        tendered = float(payment.get("tendered", 0)) if method == "cash" else grand_total
        if method == "cash" and tendered < grand_total:
            return jsonify({
                "error": f"Cash tendered ({tendered:.2f}) is less than "
                         f"total ({grand_total:.2f})."
            }), 400
        change = round_money(max(0, tendered - grand_total)) if method == "cash" else 0

        # 4. Insert sale
        timestamp = now_iso()
        cur = conn.execute(
            """INSERT INTO sales
               (cashier, subtotal, tax_rate, tax_total, grand_total,
                status, created_at, paid_at)
               VALUES (?, ?, ?, ?, ?, 'paid', ?, ?)""",
            (cashier, subtotal, tax_rate, tax_total, grand_total,
             timestamp, timestamp),
        )
        sale_id = cur.lastrowid

        # 5. Insert lines with price snapshot
        for r in resolved_lines:
            conn.execute(
                """INSERT INTO sale_lines
                   (sale_id, product_id, product_name, qty,
                    unit_price, line_total, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (sale_id, r["product_id"], r["product_name"],
                 r["qty"], r["unit_price"], r["line_total"], timestamp),
            )

        # 6. Insert payment
        conn.execute(
            """INSERT INTO payments
               (sale_id, method, amount, tendered, change, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sale_id, method, grand_total, tendered, change, timestamp),
        )

        # 7. Stock movements + quantity update
        for r in resolved_lines:
            conn.execute(
                """INSERT INTO stock_movements
                   (product_id, delta, reason, note, created_at)
                   VALUES (?, ?, 'sold', ?, ?)""",
                (r["product_id"], -r["qty"], f"POS sale #{sale_id}", timestamp),
            )
            conn.execute(
                "UPDATE products SET quantity = quantity - ?, updated_at = ? WHERE id = ?",
                (r["qty"], timestamp, r["product_id"]),
            )

        # COMMIT happens when the `with get_db()` block exits cleanly.
        # If any exception fired above, rollback happens automatically.

        # Re-fetch the complete sale to return to the client
        sale = _fetch_sale(conn, sale_id)

    return jsonify(sale), 201


@app.route("/api/sales/<int:sid>", methods=["GET"])
def get_sale(sid):
    with get_db() as conn:
        sale = _fetch_sale(conn, sid)
    if not sale:
        return jsonify({"error": "Sale not found."}), 404
    return jsonify(sale)


def _fetch_sale(conn, sid):
    """Fetch one sale with its lines and payment — the receipt source of truth."""
    sale_row = conn.execute("SELECT * FROM sales WHERE id = ?", (sid,)).fetchone()
    if not sale_row:
        return None

    lines = conn.execute(
        """SELECT id, product_id, product_name, qty, unit_price, line_total
           FROM sale_lines WHERE sale_id = ? ORDER BY id""",
        (sid,),
    ).fetchall()

    payment = conn.execute(
        """SELECT method, amount, tendered, change
           FROM payments WHERE sale_id = ?""",
        (sid,),
    ).fetchone()

    sale = row_to_dict(sale_row)
    sale["lines"] = rows_to_list(lines)
    sale["payment"] = row_to_dict(payment)
    return sale


# ─────────────────────────────────────────────
# SALES LIST — used by Stage 04's history/report, available now
# ─────────────────────────────────────────────
@app.route("/api/sales", methods=["GET"])
def list_sales():
    """Recent sales — useful for verifying the checkout works."""
    limit = min(100, max(1, request.args.get("limit", 20, type=int)))
    with get_db() as conn:
        rows = conn.execute(
            """SELECT id, cashier, subtotal, tax_total, grand_total,
                      status, created_at, paid_at
               FROM sales
               ORDER BY created_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
    return jsonify(rows_to_list(rows))


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("Database not found. Run `python seed.py` first.")
    app.run(debug=True, port=5000)

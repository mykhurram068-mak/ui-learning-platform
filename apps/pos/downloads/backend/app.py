"""
POS API — Stage 04 (Final)
Flask + SQLite. All of Stage 03, plus:
  - Refunds as reversal sales  POST /api/sales/<id>/refund
  - Z-report                   GET  /api/reports/z?date=YYYY-MM-DD
  - Hold / resume              POST /api/sales/<id>/hold, /resume
  - Sales history with filters GET  /api/sales?from=&to=&method=&cashier=
  - Product archiving          POST /api/products/<id>/archive
  - Receipt data               GET  /api/sales/<id>

Run:
    python seed.py
    python app.py       → http://localhost:5000
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime, timezone, date

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
    return round(n + 1e-9, 2)


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "pos-stage-04.html")


# ─────────────────────────────────────────────
# CATALOG (unchanged from Stage 03, plus archive awareness)
# ─────────────────────────────────────────────
@app.route("/api/products", methods=["GET"])
def list_products():
    include_empty = request.args.get("all") == "1"
    include_archived = request.args.get("archived") == "1"

    clauses = []
    if not include_empty:
        clauses.append("quantity > 0")
    if not include_archived:
        clauses.append("archived_at IS NULL")

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    with get_db() as conn:
        rows = conn.execute(
            f"""SELECT id, sku, name, category, price, quantity AS stock,
                       archived_at
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
               WHERE quantity > 0 AND archived_at IS NULL AND category IS NOT NULL
               ORDER BY category"""
        ).fetchall()
    return jsonify([r["category"] for r in rows])


@app.route("/api/products/<int:pid>/archive", methods=["POST"])
def archive_product(pid):
    with get_db() as conn:
        p = conn.execute("SELECT id FROM products WHERE id = ?", (pid,)).fetchone()
        if not p:
            return jsonify({"error": "Product not found."}), 404
        conn.execute(
            "UPDATE products SET archived_at = ?, updated_at = ? WHERE id = ?",
            (now_iso(), now_iso(), pid),
        )
        conn.commit()
    return jsonify({"ok": True})


@app.route("/api/products/<int:pid>/unarchive", methods=["POST"])
def unarchive_product(pid):
    with get_db() as conn:
        p = conn.execute("SELECT id FROM products WHERE id = ?", (pid,)).fetchone()
        if not p:
            return jsonify({"error": "Product not found."}), 404
        conn.execute(
            "UPDATE products SET archived_at = NULL, updated_at = ? WHERE id = ?",
            (now_iso(), pid),
        )
        conn.commit()
    return jsonify({"ok": True})


# ─────────────────────────────────────────────
# THE ATOMIC CHECKOUT (unchanged from Stage 03)
# ─────────────────────────────────────────────
@app.route("/api/sales", methods=["POST"])
def create_sale():
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

    with get_db() as conn:
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
                """SELECT id, name, price, quantity, archived_at
                   FROM products WHERE id = ?""",
                (pid,),
            ).fetchone()

            if not product:
                return jsonify({"error": f"Product {pid} not found."}), 404
            if product["archived_at"]:
                return jsonify({
                    "error": f'"{product["name"]}" is archived and cannot be sold.'
                }), 409
            if product["quantity"] < qty:
                return jsonify({
                    "error": f'Only {product["quantity"]} of "{product["name"]}" '
                             f'in stock (tried {qty}).'
                }), 409

            resolved_lines.append({
                "product_id": product["id"],
                "product_name": product["name"],
                "qty": qty,
                "unit_price": product["price"],
                "line_total": round_money(product["price"] * qty),
            })

        subtotal = round_money(sum(r["line_total"] for r in resolved_lines))
        tax_total = round_money(subtotal * tax_rate / 100)
        grand_total = round_money(subtotal + tax_total)

        tendered = float(payment.get("tendered", 0)) if method == "cash" else grand_total
        if method == "cash" and tendered < grand_total:
            return jsonify({
                "error": f"Cash tendered ({tendered:.2f}) is less "
                         f"than total ({grand_total:.2f})."
            }), 400
        change = round_money(max(0, tendered - grand_total)) if method == "cash" else 0

        timestamp = now_iso()
        cur = conn.execute(
            """INSERT INTO sales
               (cashier, subtotal, tax_rate, tax_total, grand_total,
                status, refund_of_sale_id, created_at, paid_at)
               VALUES (?, ?, ?, ?, ?, 'paid', NULL, ?, ?)""",
            (cashier, subtotal, tax_rate, tax_total, grand_total,
             timestamp, timestamp),
        )
        sale_id = cur.lastrowid

        for r in resolved_lines:
            conn.execute(
                """INSERT INTO sale_lines
                   (sale_id, product_id, product_name, qty,
                    unit_price, line_total, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (sale_id, r["product_id"], r["product_name"],
                 r["qty"], r["unit_price"], r["line_total"], timestamp),
            )

        conn.execute(
            """INSERT INTO payments
               (sale_id, method, amount, tendered, change, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sale_id, method, grand_total, tendered, change, timestamp),
        )

        for r in resolved_lines:
            conn.execute(
                """INSERT INTO stock_movements
                   (product_id, delta, reason, note, created_at)
                   VALUES (?, ?, 'sold', ?, ?)""",
                (r["product_id"], -r["qty"], f"POS sale #{sale_id}", timestamp),
            )
            conn.execute(
                """UPDATE products
                   SET quantity = quantity - ?, updated_at = ?
                   WHERE id = ?""",
                (r["qty"], timestamp, r["product_id"]),
            )

        sale = _fetch_sale(conn, sale_id)

    return jsonify(sale), 201


# ─────────────────────────────────────────────
# REFUND — a reversal sale. The original is untouched.
# ─────────────────────────────────────────────
@app.route("/api/sales/<int:sid>/refund", methods=["POST"])
def refund_sale(sid):
    """
    Create a reversal sale for the given original.

    Body (optional): {"note": "Customer returned damaged item"}
    Full refund only in Stage 04; partial is a future exercise.

    The original sale is NOT modified. A new sale is created with:
      - negative quantities and totals
      - refund_of_sale_id = <original_id>
      - status = 'paid'  (it's a completed transaction)
    A matching payment with negative amount is inserted.
    stock_movements get reason='refunded' with positive delta.
    products.quantity is incremented back.
    """
    data = request.get_json(silent=True) or {}
    note = (data.get("note") or "").strip() or f"Refund of sale #{sid}"

    with get_db() as conn:
        original = conn.execute(
            "SELECT * FROM sales WHERE id = ?", (sid,)
        ).fetchone()
        if not original:
            return jsonify({"error": "Sale not found."}), 404
        if original["status"] != "paid":
            return jsonify({
                "error": f"Only paid sales can be refunded (status is '{original['status']}')."
            }), 400
        if original["refund_of_sale_id"] is not None:
            return jsonify({"error": "This sale is itself a refund and cannot be refunded."}), 400

        # Guard: already refunded?
        existing_refund = conn.execute(
            "SELECT id FROM sales WHERE refund_of_sale_id = ?", (sid,)
        ).fetchone()
        if existing_refund:
            return jsonify({
                "error": f"Sale #{sid} has already been refunded (refund #{existing_refund['id']})."
            }), 409

        original_lines = conn.execute(
            "SELECT * FROM sale_lines WHERE sale_id = ?", (sid,)
        ).fetchall()
        original_payment = conn.execute(
            "SELECT * FROM payments WHERE sale_id = ?", (sid,)
        ).fetchone()
        if not original_payment:
            return jsonify({"error": "Original sale has no payment record."}), 500

        timestamp = now_iso()

        # Insert reversal sale
        cur = conn.execute(
            """INSERT INTO sales
               (cashier, subtotal, tax_rate, tax_total, grand_total,
                status, refund_of_sale_id, created_at, paid_at)
               VALUES (?, ?, ?, ?, ?, 'paid', ?, ?, ?)""",
            (
                original["cashier"],
                -original["subtotal"],
                original["tax_rate"],
                -original["tax_total"],
                -original["grand_total"],
                sid, timestamp, timestamp,
            ),
        )
        refund_id = cur.lastrowid

        # Reverse every line: negative qty, negative totals
        for line in original_lines:
            conn.execute(
                """INSERT INTO sale_lines
                   (sale_id, product_id, product_name, qty,
                    unit_price, line_total, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (refund_id, line["product_id"], line["product_name"],
                 -line["qty"], line["unit_price"], -line["line_total"], timestamp),
            )
            # Reverse the stock movement: positive delta, reason='refunded'
            conn.execute(
                """INSERT INTO stock_movements
                   (product_id, delta, reason, note, created_at)
                   VALUES (?, ?, 'refunded', ?, ?)""",
                (line["product_id"], line["qty"],
                 f"Refund of sale #{sid}", timestamp),
            )
            # Restore stock
            conn.execute(
                """UPDATE products
                   SET quantity = quantity + ?, updated_at = ?
                   WHERE id = ?""",
                (line["qty"], timestamp, line["product_id"]),
            )

        # Reversal payment
        conn.execute(
            """INSERT INTO payments
               (sale_id, method, amount, tendered, change, created_at)
               VALUES (?, ?, ?, ?, 0, ?)""",
            (refund_id, original_payment["method"],
             -original_payment["amount"],
             -original_payment["amount"], timestamp),
        )

        refund = _fetch_sale(conn, refund_id)

    refund["refund_note"] = note
    return jsonify(refund), 201


# ─────────────────────────────────────────────
# HOLD / RESUME
# ─────────────────────────────────────────────
@app.route("/api/sales/hold", methods=["POST"])
def hold_sale():
    """Park a cart for later. Unlike create_sale, this does NOT
    touch stock — a held sale isn't a completed transaction."""
    data = request.get_json(silent=True) or {}
    lines = data.get("lines") or []
    tax_rate = float(data.get("taxRate", 8.5))
    cashier = (data.get("cashier") or "Alex Rivera").strip()

    if not lines:
        return jsonify({"error": "Cannot hold an empty cart."}), 400

    with get_db() as conn:
        # Validate lines exist (no stock check — held carts don't reserve stock)
        resolved = []
        subtotal = 0.0
        for raw in lines:
            try:
                pid = int(raw["productId"])
                qty = int(raw["qty"])
            except (KeyError, TypeError, ValueError):
                return jsonify({"error": "Invalid line item."}), 400
            if qty <= 0:
                return jsonify({"error": "Quantity must be positive."}), 400

            p = conn.execute(
                "SELECT id, name, price FROM products WHERE id = ? AND archived_at IS NULL",
                (pid,),
            ).fetchone()
            if not p:
                return jsonify({"error": f"Product {pid} not found or archived."}), 404

            lt = round_money(p["price"] * qty)
            subtotal += lt
            resolved.append({
                "product_id": p["id"], "name": p["name"],
                "qty": qty, "unit_price": p["price"], "line_total": lt,
            })

        subtotal = round_money(subtotal)
        tax_total = round_money(subtotal * tax_rate / 100)
        grand_total = round_money(subtotal + tax_total)
        timestamp = now_iso()

        cur = conn.execute(
            """INSERT INTO sales
               (cashier, subtotal, tax_rate, tax_total, grand_total,
                status, refund_of_sale_id, created_at, paid_at)
               VALUES (?, ?, ?, ?, ?, 'held', NULL, ?, NULL)""",
            (cashier, subtotal, tax_rate, tax_total, grand_total, timestamp),
        )
        sale_id = cur.lastrowid

        for r in resolved:
            conn.execute(
                """INSERT INTO sale_lines
                   (sale_id, product_id, product_name, qty,
                    unit_price, line_total, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (sale_id, r["product_id"], r["name"], r["qty"],
                 r["unit_price"], r["line_total"], timestamp),
            )

        sale = _fetch_sale(conn, sale_id)

    return jsonify(sale), 201


@app.route("/api/sales/<int:sid>/resume", methods=["POST"])
def resume_sale(sid):
    """Return a held sale's lines so the frontend can load them into the cart.
    The sale stays 'held' until the client completes it (which voids it)
    or explicitly cancels it. This is the simplest correct model: the
    server doesn't track 'currently being resumed by whom.'"""
    with get_db() as conn:
        sale = conn.execute("SELECT * FROM sales WHERE id = ?", (sid,)).fetchone()
        if not sale:
            return jsonify({"error": "Sale not found."}), 404
        if sale["status"] != "held":
            return jsonify({"error": f"Sale #{sid} is not held (status '{sale['status']}')."}), 400

        sale = _fetch_sale(conn, sid)

    return jsonify(sale)


@app.route("/api/sales/<int:sid>/void", methods=["POST"])
def void_held_sale(sid):
    """Delete a held sale. Since held sales never touched stock,
    deleting the sale + its lines is safe. Only allowed for
    status='held'."""
    with get_db() as conn:
        sale = conn.execute("SELECT * FROM sales WHERE id = ?", (sid,)).fetchone()
        if not sale:
            return jsonify({"error": "Sale not found."}), 404
        if sale["status"] != "held":
            return jsonify({"error": "Only held sales can be voided."}), 400
        conn.execute("DELETE FROM sales WHERE id = ?", (sid,))
        conn.commit()
    return jsonify({"ok": True})


@app.route("/api/sales/held", methods=["GET"])
def list_held_sales():
    with get_db() as conn:
        rows = conn.execute(
            """SELECT s.id, s.cashier, s.grand_total, s.created_at,
                      (SELECT COUNT(*) FROM sale_lines WHERE sale_id = s.id) AS line_count
               FROM sales s
               WHERE s.status = 'held'
               ORDER BY s.created_at DESC"""
        ).fetchall()
    return jsonify(rows_to_list(rows))


# ─────────────────────────────────────────────
# SALES HISTORY
# ─────────────────────────────────────────────
@app.route("/api/sales", methods=["GET"])
def list_sales():
    from_date = request.args.get("from")   # YYYY-MM-DD
    to_date = request.args.get("to")       # YYYY-MM-DD
    method = request.args.get("method")
    cashier = request.args.get("cashier")
    status = request.args.get("status", "paid")
    limit = min(200, max(1, request.args.get("limit", 50, type=int)))

    clauses = ["s.status = ?"]
    params = [status]

    if from_date:
        clauses.append("s.created_at >= ?")
        params.append(from_date + "T00:00:00")
    if to_date:
        clauses.append("s.created_at <= ?")
        params.append(to_date + "T23:59:59")
    if method:
        clauses.append(
            "EXISTS (SELECT 1 FROM payments p WHERE p.sale_id = s.id AND p.method = ?)"
        )
        params.append(method)
    if cashier:
        clauses.append("s.cashier = ?")
        params.append(cashier)

    where = "WHERE " + " AND ".join(clauses)

    with get_db() as conn:
        rows = conn.execute(
            f"""SELECT s.*,
                       (SELECT method FROM payments WHERE sale_id = s.id LIMIT 1) AS method,
                       (SELECT COUNT(*) FROM sale_lines WHERE sale_id = s.id) AS line_count
                FROM sales s
                {where}
                ORDER BY s.created_at DESC
                LIMIT ?""",
            params + [limit],
        ).fetchall()

    return jsonify(rows_to_list(rows))


# ─────────────────────────────────────────────
# Z-REPORT — end-of-day reconciliation
# ─────────────────────────────────────────────
@app.route("/api/reports/z", methods=["GET"])
def z_report():
    """
    End-of-day totals for the given date (default: today UTC).
    Returns:
      gross_sales       SUM(grand_total) for paid, non-refund sales
      refunds           SUM(grand_total) for refund sales (negative)
      net_sales         gross + refunds
      tax_collected     SUM(tax_total) for paid, non-refund sales
      by_method         gross breakdown by payment method
      payments_total    SUM(amount) across all payment rows for the day
      reconciles        True if payments_total == net_sales
    """
    d = request.args.get("date") or date.today().isoformat()
    day_start = d + "T00:00:00"
    day_end   = d + "T23:59:59"

    with get_db() as conn:
        # Gross (original sales) vs refunds — split by refund_of_sale_id
        row = conn.execute(
            """SELECT
                 COALESCE(SUM(CASE WHEN refund_of_sale_id IS NULL
                                   THEN grand_total ELSE 0 END), 0) AS gross_sales,
                 COALESCE(SUM(CASE WHEN refund_of_sale_id IS NOT NULL
                                   THEN grand_total ELSE 0 END), 0) AS refunds,
                 COALESCE(SUM(CASE WHEN refund_of_sale_id IS NULL
                                   THEN tax_total ELSE 0 END), 0) AS tax_collected,
                 COUNT(CASE WHEN refund_of_sale_id IS NULL
                            AND status='paid' THEN 1 END) AS sale_count,
                 COUNT(CASE WHEN refund_of_sale_id IS NOT NULL
                            THEN 1 END) AS refund_count
               FROM sales
               WHERE status = 'paid'
                 AND created_at BETWEEN ? AND ?""",
            (day_start, day_end),
        ).fetchone()

        gross = round_money(row["gross_sales"])
        refunds = round_money(row["refunds"])
        net = round_money(gross + refunds)
        tax = round_money(row["tax_collected"])

        # Breakdown by payment method (gross only, excluding refunds —
        # a proper Z-report separates "money in" from "money out")
        method_rows = conn.execute(
            """SELECT p.method, COALESCE(SUM(p.amount), 0) AS total
               FROM payments p
               JOIN sales s ON s.id = p.sale_id
               WHERE s.status = 'paid'
                 AND s.created_at BETWEEN ? AND ?
                 AND s.refund_of_sale_id IS NULL
               GROUP BY p.method""",
            (day_start, day_end),
        ).fetchall()

        by_method = {r["method"]: round_money(r["total"]) for r in method_rows}

        # Reconciliation: sum of ALL payment rows for the day
        # (gross + refund payments, since refund payments are negative)
        payments_total_row = conn.execute(
            """SELECT COALESCE(SUM(p.amount), 0) AS total
               FROM payments p
               JOIN sales s ON s.id = p.sale_id
               WHERE s.status = 'paid'
                 AND s.created_at BETWEEN ? AND ?""",
            (day_start, day_end),
        ).fetchone()
        payments_total = round_money(payments_total_row["total"])

    reconciles = abs(payments_total - net) < 0.01

    return jsonify({
        "date": d,
        "gross_sales": gross,
        "refunds": refunds,
        "net_sales": net,
        "tax_collected": tax,
        "sale_count": row["sale_count"],
        "refund_count": row["refund_count"],
        "by_method": by_method,
        "payments_total": payments_total,
        "reconciles": reconciles,
    })


# ─────────────────────────────────────────────
# Single sale (receipt source of truth)
# ─────────────────────────────────────────────
@app.route("/api/sales/<int:sid>", methods=["GET"])
def get_sale(sid):
    with get_db() as conn:
        sale = _fetch_sale(conn, sid)
    if not sale:
        return jsonify({"error": "Sale not found."}), 404
    return jsonify(sale)


def _fetch_sale(conn, sid):
    sale_row = conn.execute("SELECT * FROM sales WHERE id = ?", (sid,)).fetchone()
    if not sale_row:
        return None
    lines = conn.execute(
        """SELECT id, product_id, product_name, qty, unit_price, line_total
           FROM sale_lines WHERE sale_id = ? ORDER BY id""",
        (sid,),
    ).fetchall()
    payment = conn.execute(
        "SELECT method, amount, tendered, change FROM payments WHERE sale_id = ?",
        (sid,),
    ).fetchone()
    sale = row_to_dict(sale_row)
    sale["lines"] = rows_to_list(lines)
    sale["payment"] = row_to_dict(payment)
    return sale


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("Database not found. Run `python seed.py` first.")
    app.run(debug=True, port=5000)

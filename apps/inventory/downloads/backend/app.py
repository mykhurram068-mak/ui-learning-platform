"""
Inventory API — Stage 03
Flask + SQLite backend for the inventory app.

Two tables: products, suppliers (FK: products.supplier_id -> suppliers.id)

Run:
    pip install -r requirements.txt
    python seed.py          # creates inventory.db + seeds data
    python app.py           # starts on http://localhost:5000
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "inventory.db")

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)  # allow the demo HTML (file:// or another port) to call the API


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


def now_iso():
    return datetime.now(timezone.utc).isoformat()


# ─────────────────────────────────────────────
# Serve the demo frontend (so you don't need a second server)
# ─────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "inventory-stage-03.html")


# ─────────────────────────────────────────────
# GET /api/products — list all, optional ?q= and ?category=
# ─────────────────────────────────────────────
@app.route("/api/products", methods=["GET"])
def list_products():
    q = (request.args.get("q") or "").strip().lower()
    category = (request.args.get("category") or "").strip().lower()

    sql = """
        SELECT p.*, s.name AS supplier_name
        FROM products p
        LEFT JOIN suppliers s ON s.id = p.supplier_id
    """
    clauses, params = [], []
    if q:
        clauses.append("(LOWER(p.name) LIKE ? OR LOWER(p.sku) LIKE ?)")
        params += [f"%{q}%", f"%{q}%"]
    if category and category != "all":
        clauses.append("LOWER(p.category) = ?")
        params.append(category)
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY p.created_at DESC"

    with get_db() as conn:
        rows = conn.execute(sql, params).fetchall()
    return jsonify([row_to_dict(r) for r in rows])


# ─────────────────────────────────────────────
# GET /api/products/<id>
# ─────────────────────────────────────────────
@app.route("/api/products/<int:pid>", methods=["GET"])
def get_product(pid):
    with get_db() as conn:
        row = conn.execute(
            """SELECT p.*, s.name AS supplier_name
               FROM products p LEFT JOIN suppliers s ON s.id = p.supplier_id
               WHERE p.id = ?""",
            (pid,),
        ).fetchone()
    if not row:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(row_to_dict(row))


# ─────────────────────────────────────────────
# POST /api/products — create
# ─────────────────────────────────────────────
@app.route("/api/products", methods=["POST"])
def create_product():
    data = request.get_json(silent=True) or {}
    error = validate_product(data, require_sku=True)
    if error:
        return jsonify({"error": error}), 400

    sku = data["sku"].strip()

    with get_db() as conn:
        # Server-side duplicate SKU check — the client check from Stage 02,
        # repeated at the boundary. Never trust the client.
        dup = conn.execute(
            "SELECT id FROM products WHERE LOWER(sku) = LOWER(?)", (sku,)
        ).fetchone()
        if dup:
            return jsonify({"error": f'SKU "{sku}" already exists.'}), 409

        cur = conn.execute(
            """INSERT INTO products
               (sku, name, category, price, cost, quantity, reorder_level,
                supplier_id, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                sku,
                data["name"].strip(),
                (data.get("category") or "Uncategorized").strip(),
                float(data["price"]),
                float(data["cost"]),
                int(data["quantity"]),
                int(data.get("reorderLevel") or 0),
                data.get("supplierId") or None,
                now_iso(),
                now_iso(),
            ),
        )
        conn.commit()
        new_id = cur.lastrowid
        row = conn.execute(
            """SELECT p.*, s.name AS supplier_name
               FROM products p LEFT JOIN suppliers s ON s.id = p.supplier_id
               WHERE p.id = ?""",
            (new_id,),
        ).fetchone()

    return jsonify(row_to_dict(row)), 201


# ─────────────────────────────────────────────
# PUT /api/products/<id> — update
# ─────────────────────────────────────────────
@app.route("/api/products/<int:pid>", methods=["PUT"])
def update_product(pid):
    data = request.get_json(silent=True) or {}
    error = validate_product(data, require_sku=True)
    if error:
        return jsonify({"error": error}), 400

    sku = data["sku"].strip()

    with get_db() as conn:
        existing = conn.execute("SELECT id FROM products WHERE id = ?", (pid,)).fetchone()
        if not existing:
            return jsonify({"error": "Product not found"}), 404

        dup = conn.execute(
            "SELECT id FROM products WHERE LOWER(sku) = LOWER(?) AND id != ?",
            (sku, pid),
        ).fetchone()
        if dup:
            return jsonify({"error": f'SKU "{sku}" already exists.'}), 409

        conn.execute(
            """UPDATE products SET
               sku = ?, name = ?, category = ?, price = ?, cost = ?,
               quantity = ?, reorder_level = ?, supplier_id = ?, updated_at = ?
               WHERE id = ?""",
            (
                sku,
                data["name"].strip(),
                (data.get("category") or "Uncategorized").strip(),
                float(data["price"]),
                float(data["cost"]),
                int(data["quantity"]),
                int(data.get("reorderLevel") or 0),
                data.get("supplierId") or None,
                now_iso(),
                pid,
            ),
        )
        conn.commit()
        row = conn.execute(
            """SELECT p.*, s.name AS supplier_name
               FROM products p LEFT JOIN suppliers s ON s.id = p.supplier_id
               WHERE p.id = ?""",
            (pid,),
        ).fetchone()

    return jsonify(row_to_dict(row))


# ─────────────────────────────────────────────
# DELETE /api/products/<id>
# ─────────────────────────────────────────────
@app.route("/api/products/<int:pid>", methods=["DELETE"])
def delete_product(pid):
    with get_db() as conn:
        existing = conn.execute("SELECT id FROM products WHERE id = ?", (pid,)).fetchone()
        if not existing:
            return jsonify({"error": "Product not found"}), 404
        conn.execute("DELETE FROM products WHERE id = ?", (pid,))
        conn.commit()
    return jsonify({"ok": True})


# ─────────────────────────────────────────────
# GET /api/suppliers — for the dropdown
# ─────────────────────────────────────────────
@app.route("/api/suppliers", methods=["GET"])
def list_suppliers():
    with get_db() as conn:
        rows = conn.execute("SELECT id, name FROM suppliers ORDER BY name").fetchall()
    return jsonify([row_to_dict(r) for r in rows])


# ─────────────────────────────────────────────
# GET /api/categories — distinct categories
# ─────────────────────────────────────────────
@app.route("/api/categories", methods=["GET"])
def list_categories():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM products WHERE category IS NOT NULL ORDER BY category"
        ).fetchall()
    return jsonify([r["category"] for r in rows])


# ─────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────
def validate_product(data, require_sku=False):
    if require_sku and not (data.get("sku") or "").strip():
        return "SKU is required."
    if not (data.get("name") or "").strip():
        return "Product name is required."
    try:
        if float(data.get("price", -1)) < 0:
            return "Price must be >= 0."
        if float(data.get("cost", -1)) < 0:
            return "Cost must be >= 0."
    except (TypeError, ValueError):
        return "Price and cost must be numbers."
    try:
        if int(data.get("quantity", -1)) < 0:
            return "Quantity must be >= 0."
    except (TypeError, ValueError):
        return "Quantity must be an integer."
    return None


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("Database not found. Run `python seed.py` first.")
    app.run(debug=True, port=5000)

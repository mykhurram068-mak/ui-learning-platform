"""
Delivery Tracking API - Stage 04 (final)
Flask + SQLite. Seven tables.

Endpoints:
  GET  /api/state                              full state
  GET  /api/deliveries                         all deliveries
  GET  /api/deliveries/active                  active deliveries (for polling)
  GET  /api/deliveries/<id>                    one delivery with events, legs, proof
  POST /api/deliveries/<id>/events             record an event (atomic)
  POST /api/deliveries/<id>/proof              attach proof of delivery
  POST /api/dispatch/bulk                      assign multiple deliveries (atomic)
  GET  /api/couriers                           courier list
  GET  /api/notifications                      recent notifications (for demo)
  GET  /api/reports/by-courier                 deliveries per courier in a date range
  GET  /api/reports/delivery-time              average delivery time
  GET  /api/reports/failure-rate               failure rate in a date range
  GET  /api/track/<code>                       public tracking (redacted)

Run:
  python seed.py
  python app.py       -> http://localhost:5000
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "delivery.db")

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)


# ---------- DB helpers ----------
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


def parse_iso(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


# ---------- State machine (Stage 04 adds retry edges) ----------
TRANSITIONS = {
    "assigned":         {"pending", "failed"},
    "picked_up":        {"assigned"},
    "in_transit":       {"picked_up"},
    "out_for_delivery": {"in_transit", "failed"},
    "delivered":        {"out_for_delivery"},
    "failed":           {"assigned", "picked_up", "in_transit", "out_for_delivery"},
}

EVENT_RESULT = {
    "assigned":         "assigned",
    "picked_up":        "picked_up",
    "in_transit":       "in_transit",
    "out_for_delivery": "out_for_delivery",
    "delivered":        "delivered",
    "failed":           "failed",
}

NOTIFY_ON = {"out_for_delivery", "delivered", "failed"}


def can_transition(current_status, event_type):
    allowed_from = TRANSITIONS.get(event_type)
    if allowed_from is None:
        return False
    return current_status in allowed_from


# ---------- Routes ----------
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "delivery-stage-04.html")


@app.route("/api/state", methods=["GET"])
def get_state():
    with get_db() as conn:
        deliveries = rows_to_list(conn.execute(
            """SELECT d.*, c.name AS customer_name, co.name AS courier_name,
                      (SELECT method FROM proof_of_delivery WHERE delivery_id = d.id) AS proof_method
               FROM deliveries d
               JOIN customers c ON c.id = d.customer_id
               LEFT JOIN couriers co ON co.id = d.courier_id
               ORDER BY d.updated_at DESC"""
        ).fetchall())
        couriers = rows_to_list(conn.execute(
            "SELECT * FROM couriers ORDER BY name"
        ).fetchall())
        recent_events = rows_to_list(conn.execute(
            "SELECT * FROM delivery_events ORDER BY occurred_at DESC LIMIT 100"
        ).fetchall())

    return jsonify({
        "deliveries": deliveries,
        "couriers": couriers,
        "events": recent_events,
    })


@app.route("/api/deliveries", methods=["GET"])
def list_deliveries():
    with get_db() as conn:
        rows = conn.execute(
            """SELECT d.*, c.name AS customer_name, co.name AS courier_name
               FROM deliveries d
               JOIN customers c ON c.id = d.customer_id
               LEFT JOIN couriers co ON co.id = d.courier_id
               ORDER BY d.updated_at DESC"""
        ).fetchall()
    return jsonify(rows_to_list(rows))


@app.route("/api/deliveries/active", methods=["GET"])
def list_active_deliveries():
    with get_db() as conn:
        rows = conn.execute(
            """SELECT d.*, c.name AS customer_name, co.name AS courier_name,
                      l.leg_index, l.started_at AS leg_started_at
               FROM deliveries d
               JOIN customers c ON c.id = d.customer_id
               LEFT JOIN couriers co ON co.id = d.courier_id
               LEFT JOIN delivery_legs l
                 ON l.delivery_id = d.id AND l.ended_at IS NULL
               WHERE d.status NOT IN ('delivered', 'cancelled')
               ORDER BY d.updated_at DESC"""
        ).fetchall()
    return jsonify(rows_to_list(rows))


@app.route("/api/deliveries/<int:did>", methods=["GET"])
def get_delivery(did):
    with get_db() as conn:
        d = conn.execute(
            """SELECT d.*, c.name AS customer_name, co.name AS courier_name
               FROM deliveries d
               JOIN customers c ON c.id = d.customer_id
               LEFT JOIN couriers co ON co.id = d.courier_id
               WHERE d.id = ?""",
            (did,),
        ).fetchone()
        if not d:
            return jsonify({"error": "Delivery not found."}), 404

        events = rows_to_list(conn.execute(
            "SELECT * FROM delivery_events WHERE delivery_id = ? ORDER BY occurred_at DESC",
            (did,),
        ).fetchall())
        legs = rows_to_list(conn.execute(
            "SELECT * FROM delivery_legs WHERE delivery_id = ? ORDER BY leg_index",
            (did,),
        ).fetchall())
        proof = row_to_dict(conn.execute(
            "SELECT * FROM proof_of_delivery WHERE delivery_id = ?", (did,)
        ).fetchone())

    result = row_to_dict(d)
    result["events"] = events
    result["legs"] = legs
    result["proof"] = proof
    return jsonify(result)


@app.route("/api/couriers", methods=["GET"])
def list_couriers():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM couriers ORDER BY name").fetchall()
    return jsonify(rows_to_list(rows))


@app.route("/api/notifications", methods=["GET"])
def list_notifications():
    with get_db() as conn:
        rows = conn.execute(
            """SELECT n.*, d.tracking_code
               FROM notifications n
               JOIN deliveries d ON d.id = n.delivery_id
               ORDER BY n.created_at DESC LIMIT 50"""
        ).fetchall()
    return jsonify(rows_to_list(rows))


# ---------- Legs + notifications helpers ----------
def _refresh_current_leg(conn, delivery_id, event_type, ts):
    current = conn.execute(
        """SELECT * FROM delivery_legs
           WHERE delivery_id = ? AND ended_at IS NULL
           ORDER BY leg_index DESC LIMIT 1""",
        (delivery_id,),
    ).fetchone()

    ends_leg = event_type in ("picked_up", "in_transit", "delivered", "failed")
    starts_leg = event_type in ("assigned", "picked_up", "in_transit")

    if current and ends_leg:
        status = "failed" if event_type == "failed" else "completed"
        conn.execute(
            "UPDATE delivery_legs SET ended_at = ?, status = ? WHERE id = ?",
            (ts, status, current["id"]),
        )

    if starts_leg:
        next_index = (current["leg_index"] + 1) if current else 0
        conn.execute(
            """INSERT INTO delivery_legs
               (delivery_id, leg_index, from_location, to_location,
                started_at, ended_at, status)
               VALUES (?, ?, NULL, NULL, ?, NULL, 'active')""",
            (delivery_id, next_index, ts),
        )


def _queue_notification(conn, delivery_id, event_type, ts):
    if event_type not in NOTIFY_ON:
        return
    d = conn.execute(
        """SELECT c.email FROM deliveries d
           JOIN customers c ON c.id = d.customer_id
           WHERE d.id = ?""",
        (delivery_id,),
    ).fetchone()
    if not d or not d["email"]:
        return
    conn.execute(
        """INSERT INTO notifications
           (delivery_id, type, recipient, status, created_at)
           VALUES (?, ?, ?, 'pending', ?)""",
        (delivery_id, event_type, d["email"], ts),
    )


def _delivery_payload(conn, did):
    d = conn.execute(
        """SELECT d.*, c.name AS customer_name, co.name AS courier_name
           FROM deliveries d
           JOIN customers c ON c.id = d.customer_id
           LEFT JOIN couriers co ON co.id = d.courier_id
           WHERE d.id = ?""",
        (did,),
    ).fetchone()
    if not d:
        return None
    result = row_to_dict(d)
    result["events"] = rows_to_list(conn.execute(
        "SELECT * FROM delivery_events WHERE delivery_id = ? ORDER BY occurred_at DESC",
        (did,),
    ).fetchall())
    result["legs"] = rows_to_list(conn.execute(
        "SELECT * FROM delivery_legs WHERE delivery_id = ? ORDER BY leg_index",
        (did,),
    ).fetchall())
    result["proof"] = row_to_dict(conn.execute(
        "SELECT * FROM proof_of_delivery WHERE delivery_id = ?", (did,)
    ).fetchone())
    return result


# ---------- Atomic event recording ----------
@app.route("/api/deliveries/<int:did>/events", methods=["POST"])
def record_event(did):
    data = request.get_json(silent=True) or {}
    event_type = data.get("type")
    note = (data.get("note") or "").strip() or None
    courier_id = data.get("courierId")

    if event_type not in EVENT_RESULT:
        return jsonify({"error": "Unknown event type."}), 400

    with get_db() as conn:
        delivery = conn.execute(
            "SELECT * FROM deliveries WHERE id = ?", (did,)
        ).fetchone()
        if not delivery:
            return jsonify({"error": "Delivery not found."}), 404

        if not can_transition(delivery["status"], event_type):
            return jsonify({
                "error": "Cannot " + event_type.replace("_", " ") +
                         " from status '" + delivery["status"] + "'."
            }), 409

        ts = now_iso()

        conn.execute(
            """INSERT INTO delivery_events
               (delivery_id, type, location, note, occurred_at, created_at, created_by)
               VALUES (?, ?, NULL, ?, ?, ?, 'api')""",
            (did, event_type, note, ts, ts),
        )

        new_status = EVENT_RESULT[event_type]
        conn.execute(
            "UPDATE deliveries SET status = ?, updated_at = ? WHERE id = ?",
            (new_status, ts, did),
        )

        if event_type == "assigned" and courier_id:
            cid = int(courier_id)
            c = conn.execute("SELECT id FROM couriers WHERE id = ?", (cid,)).fetchone()
            if not c:
                return jsonify({"error": "Courier not found."}), 404
            conn.execute(
                "UPDATE deliveries SET courier_id = ? WHERE id = ?", (cid, did)
            )
            conn.execute(
                "UPDATE couriers SET status = 'on_delivery' WHERE id = ?", (cid,)
            )

        if event_type == "delivered" and delivery["courier_id"]:
            remaining = conn.execute(
                """SELECT COUNT(*) FROM deliveries
                   WHERE courier_id = ?
                     AND status NOT IN ('delivered', 'cancelled', 'failed')""",
                (delivery["courier_id"],),
            ).fetchone()[0]
            if remaining == 0:
                conn.execute(
                    "UPDATE couriers SET status = 'available' WHERE id = ?",
                    (delivery["courier_id"],),
                )

        _refresh_current_leg(conn, did, event_type, ts)
        _queue_notification(conn, did, event_type, ts)
        conn.commit()

        return jsonify(_delivery_payload(conn, did)), 201


# ---------- Proof of delivery ----------
@app.route("/api/deliveries/<int:did>/proof", methods=["POST"])
def attach_proof(did):
    data = request.get_json(silent=True) or {}
    method = data.get("method")
    reference = (data.get("reference") or "").strip()
    note = (data.get("note") or "").strip() or None

    if method not in ("photo", "signature", "otp"):
        return jsonify({"error": "method must be photo, signature, or otp."}), 400
    if not reference:
        return jsonify({"error": "reference is required."}), 400

    with get_db() as conn:
        d = conn.execute(
            "SELECT * FROM deliveries WHERE id = ?", (did,)
        ).fetchone()
        if not d:
            return jsonify({"error": "Delivery not found."}), 404
        if d["status"] != "delivered":
            return jsonify({
                "error": "Proof can only be attached to a delivered delivery."
            }), 409

        existing = conn.execute(
            "SELECT id FROM proof_of_delivery WHERE delivery_id = ?", (did,)
        ).fetchone()
        if existing:
            return jsonify({"error": "Proof already recorded for this delivery."}), 409

        ts = now_iso()
        conn.execute(
            """INSERT INTO proof_of_delivery
               (delivery_id, method, reference, note, captured_at, captured_by)
               VALUES (?, ?, ?, ?, ?, 'courier')""",
            (did, method, reference, note, ts),
        )
        conn.commit()

        return jsonify(_delivery_payload(conn, did)), 201


# ---------- Bulk dispatch ----------
@app.route("/api/dispatch/bulk", methods=["POST"])
def bulk_dispatch():
    data = request.get_json(silent=True) or {}
    delivery_ids = data.get("deliveryIds") or []
    courier_id = data.get("courierId")

    if not delivery_ids or not courier_id:
        return jsonify({"error": "deliveryIds and courierId are required."}), 400

    try:
        courier_id = int(courier_id)
    except (TypeError, ValueError):
        return jsonify({"error": "courierId must be an integer."}), 400

    with get_db() as conn:
        courier = conn.execute(
            "SELECT * FROM couriers WHERE id = ?", (courier_id,)
        ).fetchone()
        if not courier:
            return jsonify({"error": "Courier not found."}), 404

        # Validate all before any write
        for did in delivery_ids:
            try:
                did_int = int(did)
            except (TypeError, ValueError):
                return jsonify({"error": "Invalid delivery id."}), 400
            d = conn.execute(
                "SELECT * FROM deliveries WHERE id = ?", (did_int,)
            ).fetchone()
            if not d:
                return jsonify({"error": "Delivery " + str(did_int) + " not found."}), 404
            if d["status"] != "pending":
                return jsonify({
                    "error": "Delivery " + str(did_int) + " is " + d["status"] +
                             ", not pending. Bulk dispatch requires all pending."
                }), 409

        # All valid - do all writes
        ts = now_iso()
        for did in delivery_ids:
            did_int = int(did)
            conn.execute(
                """INSERT INTO delivery_events
                   (delivery_id, type, location, note, occurred_at, created_at, created_by)
                   VALUES (?, 'assigned', NULL, ?, ?, ?, 'api')""",
                (did_int, "Bulk dispatch to " + courier["name"], ts, ts),
            )
            conn.execute(
                "UPDATE deliveries SET status = 'assigned', courier_id = ?, updated_at = ? WHERE id = ?",
                (courier_id, ts, did_int),
            )
            _refresh_current_leg(conn, did_int, "assigned", ts)

        conn.execute(
            "UPDATE couriers SET status = 'on_delivery' WHERE id = ?", (courier_id,)
        )
        conn.commit()

    return jsonify({"ok": True, "count": len(delivery_ids)}), 200


# ---------- Reports ----------
def _date_range():
    from_date = request.args.get("from")
    to_date = request.args.get("to")
    if not from_date or not to_date:
        return None, None
    return from_date + "T00:00:00", to_date + "T23:59:59"


@app.route("/api/reports/by-courier", methods=["GET"])
def report_by_courier():
    start, end = _date_range()
    if not start:
        return jsonify({"error": "from and to are required."}), 400

    with get_db() as conn:
        rows = conn.execute(
            """SELECT co.name AS courier_name,
                      COUNT(CASE WHEN d.status = 'delivered' THEN 1 END) AS delivered,
                      COUNT(CASE WHEN d.status = 'failed'    THEN 1 END) AS failed,
                      COUNT(*) AS total
               FROM deliveries d
               LEFT JOIN couriers co ON co.id = d.courier_id
               WHERE d.updated_at BETWEEN ? AND ?
               GROUP BY co.name
               ORDER BY delivered DESC""",
            (start, end),
        ).fetchall()

    result = []
    for r in rows:
        total = r["total"] or 0
        rate = (r["failed"] / total * 100) if total > 0 else 0
        result.append({
            "courier": r["courier_name"] or "Unassigned",
            "delivered": r["delivered"],
            "failed": r["failed"],
            "total": total,
            "failureRate": round(rate, 1),
        })
    return jsonify(result)


@app.route("/api/reports/delivery-time", methods=["GET"])
def report_delivery_time():
    start, end = _date_range()
    if not start:
        return jsonify({"error": "from and to are required."}), 400

    with get_db() as conn:
        rows = conn.execute(
            """SELECT co.name AS courier_name,
                      d.id, d.created_at,
                      (SELECT occurred_at FROM delivery_events
                       WHERE delivery_id = d.id AND type = 'delivered'
                       ORDER BY occurred_at DESC LIMIT 1) AS delivered_at
               FROM deliveries d
               LEFT JOIN couriers co ON co.id = d.courier_id
               WHERE d.status = 'delivered'
                 AND d.updated_at BETWEEN ? AND ?""",
            (start, end),
        ).fetchall()

    by_courier = {}
    for r in rows:
        if not r["delivered_at"]:
            continue
        try:
            mins = (parse_iso(r["delivered_at"]) - parse_iso(r["created_at"])).total_seconds() / 60
        except (ValueError, TypeError):
            continue
        key = r["courier_name"] or "Unassigned"
        by_courier.setdefault(key, []).append(mins)

    result = []
    for name, mins in by_courier.items():
        avg = sum(mins) / len(mins) if mins else 0
        result.append({
            "courier": name,
            "deliveredCount": len(mins),
            "avgMinutes": round(avg, 1),
            "avgHours": round(avg / 60, 2),
        })
    result.sort(key=lambda r: r["avgMinutes"])
    return jsonify(result)


@app.route("/api/reports/failure-rate", methods=["GET"])
def report_failure_rate():
    start, end = _date_range()
    if not start:
        return jsonify({"error": "from and to are required."}), 400

    with get_db() as conn:
        row = conn.execute(
            """SELECT COUNT(*) AS total,
                      COUNT(CASE WHEN status = 'failed' THEN 1 END) AS failed,
                      COUNT(CASE WHEN status = 'delivered' THEN 1 END) AS delivered
               FROM deliveries
               WHERE updated_at BETWEEN ? AND ?""",
            (start, end),
        ).fetchone()

    total = row["total"] or 0
    failed = row["failed"] or 0
    rate = (failed / total * 100) if total > 0 else 0
    return jsonify({
        "total": total,
        "failed": failed,
        "delivered": row["delivered"],
        "failureRate": round(rate, 1),
    })


# ---------- Public tracking ----------
@app.route("/api/track/<code>", methods=["GET"])
def track(code):
    with get_db() as conn:
        d = conn.execute(
            """SELECT d.id, d.tracking_code, d.destination, d.status, d.priority,
                      c.name AS courier_name
               FROM deliveries d
               LEFT JOIN couriers c ON c.id = d.courier_id
               WHERE d.tracking_code = ?""",
            (code,),
        ).fetchone()

        if not d:
            return jsonify({"error": "Not found."}), 404

        events = rows_to_list(conn.execute(
            """SELECT type, note, occurred_at
               FROM delivery_events WHERE delivery_id = ?
               ORDER BY occurred_at DESC""",
            (d["id"],),
        ).fetchall())
        proof = row_to_dict(conn.execute(
            "SELECT method, captured_at FROM proof_of_delivery WHERE delivery_id = ?",
            (d["id"],),
        ).fetchone())

    courier = d["courier_name"] or "Unassigned"
    if courier != "Unassigned":
        parts = courier.split(" ")
        if len(parts) > 1:
            courier = parts[0] + " " + parts[-1][0] + "."

    return jsonify({
        "trackingCode": d["tracking_code"],
        "destination": d["destination"],
        "status": d["status"],
        "priority": d["priority"],
        "courier": courier,
        "events": events,
        "proof": proof,
    })


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("Database not found. Run `python seed.py` first.")
    app.run(debug=True, port=5000)

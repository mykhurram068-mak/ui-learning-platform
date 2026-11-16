"""
Delivery Tracking API - Stage 03
Flask + SQLite. Five tables.

Endpoints:
  GET  /api/state                       full state (deliveries, couriers, recent events)
  GET  /api/deliveries                  list all deliveries
  GET  /api/deliveries/<id>             one delivery with events and legs
  POST /api/deliveries/<id>/events      record an event (atomic: insert + status + leg)
  GET  /api/deliveries/active           active deliveries for the dispatcher
  GET  /api/couriers                    courier list
  GET  /api/track/<code>                public tracking (redacted)

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


# ---------- State machine ----------
TRANSITIONS = {
    "assigned":         {"pending"},
    "picked_up":        {"assigned"},
    "in_transit":       {"picked_up"},
    "out_for_delivery": {"in_transit"},
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


def can_transition(current_status, event_type):
    allowed_from = TRANSITIONS.get(event_type)
    if allowed_from is None:
        return False
    return current_status in allowed_from


# ---------- Routes ----------
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "delivery-stage-03.html")


@app.route("/api/state", methods=["GET"])
def get_state():
    with get_db() as conn:
        deliveries = rows_to_list(conn.execute(
            """SELECT d.*, c.name AS customer_name, co.name AS courier_name
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
               WHERE d.status NOT IN ('delivered', 'cancelled', 'failed')
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

    result = row_to_dict(d)
    result["events"] = events
    result["legs"] = legs
    return jsonify(result)


@app.route("/api/couriers", methods=["GET"])
def list_couriers():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM couriers ORDER BY name").fetchall()
    return jsonify(rows_to_list(rows))


# ---------- Atomic event recording ----------
def _refresh_current_leg(conn, delivery_id, event_type, ts):
    """Update or close the current leg; open a new one if the event starts one."""
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
    return result


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

        # Atomic block: all writes commit together or not at all
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
                "UPDATE deliveries SET courier_id = ? WHERE id = ?",
                (cid, did),
            )
            conn.execute(
                "UPDATE couriers SET status = 'on_delivery' WHERE id = ?",
                (cid,),
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
        conn.commit()

        return jsonify(_delivery_payload(conn, did)), 201


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
    })


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("Database not found. Run `python seed.py` first.")
    app.run(debug=True, port=5000)

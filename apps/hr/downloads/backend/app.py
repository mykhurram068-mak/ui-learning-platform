"""
HR Attendance API - Stage 03
Flask + SQLite. Three tables: employees, attendance_events, shifts.

- attendance_events: append-only log of clock-ins, outs, breaks
- shifts: derived cache, one row per (employee, date), upserted on every event
- employees: the roster, with archived_at for former employees

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
DB_PATH = os.path.join(BASE_DIR, "hr.db")

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


def diff_minutes(a_iso, b_iso):
    a = datetime.fromisoformat(a_iso.replace("Z", "+00:00"))
    b = datetime.fromisoformat(b_iso.replace("Z", "+00:00"))
    return int(round((b - a).total_seconds() / 60))


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "hr-stage-03.html")


# ---------- Derivation ----------
def derive_shift(events, employee_id):
    """
    Walk events in chronological order, produce a shift summary.

    Returns:
      {
        date, clock_in_at, clock_out_at,
        break_minutes, minutes_worked, status
      }
    status is internal: 'not-started' | 'working' | 'on-break' | 'finished'
    """
    evs = sorted(
        [e for e in events if e["employee_id"] == employee_id],
        key=lambda e: e["occurred_at"],
    )

    clock_in = None
    clock_out = None
    break_minutes = 0
    break_start = None
    status = "not-started"

    for e in evs:
        t = e["type"]
        if t in ("in", "manual_in"):
            if status in ("not-started", "finished"):
                clock_in = e["occurred_at"]
                clock_out = None
                status = "working"
        elif t == "break_start":
            if status == "working":
                break_start = e["occurred_at"]
                status = "on-break"
        elif t == "break_end":
            if status == "on-break" and break_start:
                break_minutes += diff_minutes(break_start, e["occurred_at"])
                break_start = None
                status = "working"
        elif t in ("out", "manual_out"):
            if status in ("working", "on-break"):
                if break_start:
                    break_minutes += diff_minutes(break_start, e["occurred_at"])
                    break_start = None
                clock_out = e["occurred_at"]
                status = "finished"

    minutes_worked = 0
    if clock_in:
        end = clock_out or now_iso()
        minutes_worked = diff_minutes(clock_in, end) - break_minutes
        if minutes_worked < 0:
            minutes_worked = 0

    shift_date = evs[0]["occurred_at"][:10] if evs else None

    return {
        "date": shift_date,
        "clock_in_at": clock_in,
        "clock_out_at": clock_out,
        "break_minutes": break_minutes,
        "minutes_worked": minutes_worked,
        "status": status,
    }


def _refresh_shift(conn, employee_id):
    """Re-derive this employee's current shift and upsert the shifts row."""
    events = conn.execute(
        "SELECT * FROM attendance_events WHERE employee_id = ? ORDER BY occurred_at",
        (employee_id,),
    ).fetchall()

    shift = derive_shift(rows_to_list(events), employee_id)

    if shift["status"] == "not-started" or not shift["date"]:
        return

    table_status = "open" if shift["status"] in ("working", "on-break") else "closed"
    ts = now_iso()

    conn.execute(
        """INSERT INTO shifts
           (employee_id, date, clock_in_at, clock_out_at,
            break_minutes, minutes_worked, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(employee_id, date) DO UPDATE SET
             clock_in_at    = excluded.clock_in_at,
             clock_out_at   = excluded.clock_out_at,
             break_minutes  = excluded.break_minutes,
             minutes_worked = excluded.minutes_worked,
             status         = excluded.status""",
        (
            employee_id,
            shift["date"],
            shift["clock_in_at"],
            shift["clock_out_at"],
            shift["break_minutes"],
            shift["minutes_worked"],
            table_status,
            ts,
        ),
    )


# ---------- State payload ----------
def _state_payload(conn):
    """Everything the client needs to render, in one response."""
    employees = rows_to_list(conn.execute(
        "SELECT id, name, email, role, hourly_rate, hired_at, archived_at "
        "FROM employees ORDER BY name"
    ).fetchall())

    today_str = datetime.now(timezone.utc).date().isoformat()

    events = rows_to_list(conn.execute(
        "SELECT * FROM attendance_events "
        "WHERE occurred_at >= ? "
        "ORDER BY occurred_at DESC",
        (today_str + "T00:00:00",),
    ).fetchall())

    shifts = rows_to_list(conn.execute(
        "SELECT * FROM shifts WHERE date = ? ORDER BY employee_id",
        (today_str,),
    ).fetchall())

    return {
        "employees": employees,
        "events": events,
        "shifts": shifts,
        "today": today_str,
    }


# ---------- Routes ----------
@app.route("/api/state", methods=["GET"])
def get_state():
    with get_db() as conn:
        return jsonify(_state_payload(conn))


@app.route("/api/employees", methods=["GET"])
def list_employees():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, name, email, role, hourly_rate, hired_at, archived_at "
            "FROM employees ORDER BY name"
        ).fetchall()
    return jsonify(rows_to_list(rows))


def _find_employee(conn, employee_id):
    return conn.execute(
        "SELECT * FROM employees WHERE id = ? AND archived_at IS NULL",
        (employee_id,),
    ).fetchone()


def _employee_events(conn, employee_id):
    rows = conn.execute(
        "SELECT * FROM attendance_events WHERE employee_id = ? ORDER BY occurred_at",
        (employee_id,),
    ).fetchall()
    return rows_to_list(rows)


def _insert_event(conn, employee_id, event_type, note=None):
    ts = now_iso()
    conn.execute(
        "INSERT INTO attendance_events "
        "(employee_id, type, occurred_at, note, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (employee_id, event_type, ts, note, ts),
    )


@app.route("/api/clock-in", methods=["POST"])
def clock_in():
    data = request.get_json(silent=True) or {}
    employee_id = int(data.get("employeeId") or 0)
    if not employee_id:
        return jsonify({"error": "employeeId is required."}), 400

    with get_db() as conn:
        emp = _find_employee(conn, employee_id)
        if not emp:
            return jsonify({"error": "Employee not found."}), 404

        current = derive_shift(_employee_events(conn, employee_id), employee_id)
        if current["status"] in ("working", "on-break"):
            return jsonify({
                "error": "Already clocked in.",
                "shift": current,
            }), 409

        _insert_event(conn, employee_id, "in")
        _refresh_shift(conn, employee_id)
        conn.commit()

        return jsonify(_state_payload(conn)), 201


@app.route("/api/clock-out", methods=["POST"])
def clock_out():
    data = request.get_json(silent=True) or {}
    employee_id = int(data.get("employeeId") or 0)
    if not employee_id:
        return jsonify({"error": "employeeId is required."}), 400

    with get_db() as conn:
        emp = _find_employee(conn, employee_id)
        if not emp:
            return jsonify({"error": "Employee not found."}), 404

        current = derive_shift(_employee_events(conn, employee_id), employee_id)
        if current["status"] not in ("working", "on-break"):
            return jsonify({
                "error": "Not currently clocked in.",
                "shift": current,
            }), 409

        _insert_event(conn, employee_id, "out")
        _refresh_shift(conn, employee_id)
        conn.commit()

        return jsonify(_state_payload(conn)), 201


@app.route("/api/break", methods=["POST"])
def toggle_break():
    data = request.get_json(silent=True) or {}
    employee_id = int(data.get("employeeId") or 0)
    if not employee_id:
        return jsonify({"error": "employeeId is required."}), 400

    with get_db() as conn:
        emp = _find_employee(conn, employee_id)
        if not emp:
            return jsonify({"error": "Employee not found."}), 404

        current = derive_shift(_employee_events(conn, employee_id), employee_id)

        if current["status"] == "working":
            _insert_event(conn, employee_id, "break_start")
        elif current["status"] == "on-break":
            _insert_event(conn, employee_id, "break_end")
        else:
            return jsonify({
                "error": "Not working - cannot start or end a break.",
                "shift": current,
            }), 409

        _refresh_shift(conn, employee_id)
        conn.commit()

        return jsonify(_state_payload(conn)), 201


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("Database not found. Run `python seed.py` first.")
    app.run(debug=True, port=5000)

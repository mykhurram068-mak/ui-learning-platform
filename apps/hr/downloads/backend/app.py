"""
HR Attendance API - Stage 04 (final)
Flask + SQLite. Four tables: employees, attendance_events, shifts, scheduled_shifts.

Endpoints:
  GET  /api/state              full state (employees, today's events, today's shifts)
  GET  /api/employees          employee list
  POST /api/clock-in           insert 'in' (409 if already working)
  POST /api/clock-out          insert 'out' (409 if not working)
  POST /api/break              toggle break (409 if not working)
  POST /api/correction         insert manual_in or manual_out with a note
  GET  /api/timesheet?week=    week grid: employees x days x minutes
  GET  /api/roster/compare?week=  scheduled vs actual, with late minutes
  POST /api/approve-week       flip closed shifts to approved (409 if any open)
  POST /api/reopen-week        flip approved shifts to closed
  GET  /api/report?week=       per-employee totals, overtime, late, absent
  GET  /api/schedule?week=     raw scheduled shifts for the week

Run:
  python seed.py
  python app.py       -> http://localhost:5000
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime, timezone, timedelta, date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "hr.db")

OVERTIME_THRESHOLD_MINUTES = 40 * 60

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


def _add_days(date_str, days):
    d = datetime.fromisoformat(date_str + "T00:00:00")
    return (d + timedelta(days=days)).date().isoformat()


def _current_week_start():
    """Monday of the current week, in UTC."""
    today = datetime.now(timezone.utc).date()
    monday = today - timedelta(days=today.weekday())
    return monday.isoformat()


def _week_start_for(date_str):
    d = datetime.fromisoformat(date_str + "T00:00:00").date()
    monday = d - timedelta(days=d.weekday())
    return monday.isoformat()


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "hr-stage-04.html")


# ---------- Derivation ----------
def derive_shift(events, employee_id):
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
    events = conn.execute(
        "SELECT * FROM attendance_events WHERE employee_id = ? ORDER BY occurred_at",
        (employee_id,),
    ).fetchall()

    shift = derive_shift(rows_to_list(events), employee_id)

    if shift["status"] == "not-started" or not shift["date"]:
        return

    table_status = "open" if shift["status"] in ("working", "on-break") else "closed"
    ts = now_iso()

    # Preserve 'approved' status - don't downgrade an approved week's shift
    existing = conn.execute(
        "SELECT status FROM shifts WHERE employee_id = ? AND date = ?",
        (employee_id, shift["date"]),
    ).fetchone()
    if existing and existing["status"] == "approved":
        table_status = "approved"

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
    employees = rows_to_list(conn.execute(
        "SELECT id, name, email, role, hourly_rate, hired_at, archived_at "
        "FROM employees ORDER BY name"
    ).fetchall())

    today_str = datetime.now(timezone.utc).date().isoformat()

    events = rows_to_list(conn.execute(
        "SELECT * FROM attendance_events WHERE occurred_at >= ? "
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


def _list_active_employees(conn):
    return rows_to_list(conn.execute(
        "SELECT id, name, email, role, hourly_rate, hired_at "
        "FROM employees WHERE archived_at IS NULL ORDER BY name"
    ).fetchall())


# ---------- State / employees ----------
@app.route("/api/state", methods=["GET"])
def get_state():
    with get_db() as conn:
        return jsonify(_state_payload(conn))


@app.route("/api/employees", methods=["GET"])
def list_employees():
    with get_db() as conn:
        return jsonify(_list_active_employees(conn))


# ---------- Clock actions ----------
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


def _insert_event(conn, employee_id, event_type, note=None, occurred_at=None):
    ts = now_iso()
    at = occurred_at or ts
    conn.execute(
        "INSERT INTO attendance_events "
        "(employee_id, type, occurred_at, note, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (employee_id, event_type, at, note, ts),
    )


@app.route("/api/clock-in", methods=["POST"])
def clock_in():
    data = request.get_json(silent=True) or {}
    employee_id = int(data.get("employeeId") or 0)
    if not employee_id:
        return jsonify({"error": "employeeId is required."}), 400

    with get_db() as conn:
        if not _find_employee(conn, employee_id):
            return jsonify({"error": "Employee not found."}), 404

        current = derive_shift(_employee_events(conn, employee_id), employee_id)
        if current["status"] in ("working", "on-break"):
            return jsonify({"error": "Already clocked in.", "shift": current}), 409

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
        if not _find_employee(conn, employee_id):
            return jsonify({"error": "Employee not found."}), 404

        current = derive_shift(_employee_events(conn, employee_id), employee_id)
        if current["status"] not in ("working", "on-break"):
            return jsonify({"error": "Not currently clocked in.", "shift": current}), 409

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
        if not _find_employee(conn, employee_id):
            return jsonify({"error": "Employee not found."}), 404

        current = derive_shift(_employee_events(conn, employee_id), employee_id)

        if current["status"] == "working":
            _insert_event(conn, employee_id, "break_start")
        elif current["status"] == "on-break":
            _insert_event(conn, employee_id, "break_end")
        else:
            return jsonify({"error": "Not working - cannot toggle break.", "shift": current}), 409

        _refresh_shift(conn, employee_id)
        conn.commit()
        return jsonify(_state_payload(conn)), 201


# ---------- Corrections ----------
@app.route("/api/correction", methods=["POST"])
def add_correction():
    data = request.get_json(silent=True) or {}
    employee_id = int(data.get("employeeId") or 0)
    event_type = data.get("type")
    occurred_at = data.get("occurredAt")
    note = (data.get("note") or "").strip()

    if event_type not in ("manual_in", "manual_out"):
        return jsonify({"error": "type must be manual_in or manual_out."}), 400
    if not employee_id or not occurred_at:
        return jsonify({"error": "employeeId and occurredAt required."}), 400
    if not note:
        return jsonify({"error": "A note is required for corrections."}), 400

    with get_db() as conn:
        if not _find_employee(conn, employee_id):
            return jsonify({"error": "Employee not found."}), 404

        week_start = _week_start_for(occurred_at[:10])
        week_end = _add_days(week_start, 6)
        approved = conn.execute(
            "SELECT 1 FROM shifts WHERE employee_id = ? "
            "AND date BETWEEN ? AND ? AND status = 'approved' LIMIT 1",
            (employee_id, week_start, week_end),
        ).fetchone()
        if approved:
            return jsonify({
                "error": "That week is approved. Reopen it before correcting."
            }), 409

        _insert_event(conn, employee_id, event_type, note=note, occurred_at=occurred_at)
        _refresh_shift(conn, employee_id)
        conn.commit()
        return jsonify(_state_payload(conn)), 201


# ---------- Timesheet ----------
@app.route("/api/timesheet", methods=["GET"])
def get_timesheet():
    week_start = request.args.get("week") or _current_week_start()
    week_end = _add_days(week_start, 6)

    with get_db() as conn:
        rows = conn.execute(
            """SELECT employee_id, date,
                      SUM(minutes_worked) AS minutes,
                      MIN(status)         AS status
               FROM shifts
               WHERE date BETWEEN ? AND ?
               GROUP BY employee_id, date""",
            (week_start, week_end),
        ).fetchall()

        employees = _list_active_employees(conn)

    grid = {}
    for emp in employees:
        grid[emp["id"]] = {"name": emp["name"], "days": {}}

    for r in rows:
        if r["employee_id"] in grid:
            grid[r["employee_id"]]["days"][r["date"]] = {
                "minutes": r["minutes"],
                "status": r["status"],
            }

    return jsonify({
        "week_start": week_start,
        "week_end": week_end,
        "employees": list(grid.values()),
    })


# ---------- Roster ----------
@app.route("/api/schedule", methods=["GET"])
def get_schedule():
    week_start = request.args.get("week") or _current_week_start()
    week_end = _add_days(week_start, 6)

    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM scheduled_shifts "
            "WHERE date BETWEEN ? AND ? "
            "ORDER BY date, start_at",
            (week_start, week_end),
        ).fetchall()
    return jsonify(rows_to_list(rows))


@app.route("/api/roster/compare", methods=["GET"])
def roster_compare():
    week_start = request.args.get("week") or _current_week_start()
    week_end = _add_days(week_start, 6)

    with get_db() as conn:
        rows = conn.execute(
            """SELECT s.employee_id, s.date,
                      s.start_at  AS sched_start,
                      s.end_at    AS sched_end,
                      w.clock_in_at  AS actual_in,
                      w.clock_out_at AS actual_out
               FROM scheduled_shifts s
               LEFT JOIN shifts w
                 ON w.employee_id = s.employee_id
                AND w.date = s.date
               WHERE s.date BETWEEN ? AND ?
               ORDER BY s.date, s.employee_id""",
            (week_start, week_end),
        ).fetchall()

    result = []
    for r in rows:
        late_minutes = 0
        if r["actual_in"] and r["sched_start"]:
            late_minutes = max(0, diff_minutes(r["sched_start"], r["actual_in"]))
        result.append({
            "employee_id": r["employee_id"],
            "date": r["date"],
            "scheduled": {"start": r["sched_start"], "end": r["sched_end"]},
            "actual": {"in": r["actual_in"], "out": r["actual_out"]},
            "late_minutes": late_minutes,
            "absent": r["actual_in"] is None,
        })
    return jsonify(result)


# ---------- Approval ----------
@app.route("/api/approve-week", methods=["POST"])
def approve_week():
    data = request.get_json(silent=True) or {}
    week_start = data.get("weekStart")
    if not week_start:
        return jsonify({"error": "weekStart is required."}), 400
    week_end = _add_days(week_start, 6)

    with get_db() as conn:
        open_count = conn.execute(
            "SELECT COUNT(*) FROM shifts WHERE date BETWEEN ? AND ? AND status = 'open'",
            (week_start, week_end),
        ).fetchone()[0]
        if open_count > 0:
            return jsonify({
                "error": "Cannot approve - " + str(open_count) + " shifts still open."
            }), 409

        conn.execute(
            "UPDATE shifts SET status = 'approved' "
            "WHERE date BETWEEN ? AND ? AND status = 'closed'",
            (week_start, week_end),
        )
        conn.commit()

    return jsonify({"ok": True, "week_start": week_start}), 200


@app.route("/api/reopen-week", methods=["POST"])
def reopen_week():
    data = request.get_json(silent=True) or {}
    week_start = data.get("weekStart")
    if not week_start:
        return jsonify({"error": "weekStart is required."}), 400
    week_end = _add_days(week_start, 6)

    with get_db() as conn:
        conn.execute(
            "UPDATE shifts SET status = 'closed' "
            "WHERE date BETWEEN ? AND ? AND status = 'approved'",
            (week_start, week_end),
        )
        conn.commit()

    return jsonify({"ok": True, "week_start": week_start}), 200


# ---------- Report ----------
@app.route("/api/report", methods=["GET"])
def get_report():
    week_start = request.args.get("week") or _current_week_start()
    week_end = _add_days(week_start, 6)

    with get_db() as conn:
        rows = conn.execute(
            """SELECT e.id   AS employee_id,
                      e.name AS employee_name,
                      COALESCE(SUM(w.minutes_worked), 0) AS total_minutes,
                      SUM(CASE WHEN s.id IS NOT NULL
                                AND w.clock_in_at IS NULL
                               THEN 1 ELSE 0 END)      AS absent_count,
                      SUM(CASE WHEN w.clock_in_at IS NOT NULL
                                AND s.start_at IS NOT NULL
                                AND w.clock_in_at > s.start_at
                               THEN 1 ELSE 0 END)      AS late_count
               FROM employees e
               LEFT JOIN shifts w
                 ON w.employee_id = e.id
                AND w.date BETWEEN ? AND ?
               LEFT JOIN scheduled_shifts s
                 ON s.employee_id = e.id
                AND s.date = w.date
               WHERE e.archived_at IS NULL
               GROUP BY e.id, e.name
               ORDER BY e.name""",
            (week_start, week_end),
        ).fetchall()

    result = []
    for r in rows:
        total = r["total_minutes"] or 0
        overtime = max(0, total - OVERTIME_THRESHOLD_MINUTES)
        result.append({
            "employee_id": r["employee_id"],
            "employee_name": r["employee_name"],
            "total_minutes": total,
            "overtime_minutes": overtime,
            "absent_count": r["absent_count"],
            "late_count": r["late_count"],
        })
    return jsonify(result)


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("Database not found. Run `python seed.py` first.")
    app.run(debug=True, port=5000)

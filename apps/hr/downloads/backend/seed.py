"""
Creates hr.db, applies schema.sql, and seeds sample data.
Run once: python seed.py
"""

from datetime import datetime, timezone, timedelta
from database import init_db, connect


def now():
    return datetime.now(timezone.utc).isoformat()


def today_at(hour, minute=0, days_ago=0):
    """ISO timestamp for today at HH:MM UTC, optionally N days ago."""
    now_utc = datetime.now(timezone.utc)
    base = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    base = base - timedelta(days=days_ago)
    return (base + timedelta(hours=hour, minutes=minute)).isoformat()


def seed():
    init_db()
    conn = connect()

    employees = [
        ("Jane Smith",    "jane@example.com",    "manager",  45.00),
        ("Marcus Chen",   "marcus@example.com",  "employee", 28.00),
        ("Priya Raman",   "priya@example.com",   "employee", 28.00),
        ("David Wu",      "david@example.com",   "employee", 30.00),
        ("Sofia Alvarez", "sofia@example.com",   "employee", 26.00),
        ("Tariq Khan",    "tariq@example.com",   "employee", 27.00),
    ]
    for name, email, role, rate in employees:
        conn.execute(
            "INSERT INTO employees "
            "(name, email, role, hourly_rate, hired_at, archived_at) "
            "VALUES (?, ?, ?, ?, ?, NULL)",
            (name, email, role, rate, now()),
        )
    conn.commit()

    ids = {r["name"]: r["id"] for r in conn.execute(
        "SELECT id, name FROM employees"
    ).fetchall()}

    # Today's events: a realistic morning
    events = [
        # employee, type, occurred_at
        (ids["Marcus Chen"],   "in",          today_at(8, 58)),
        (ids["David Wu"],      "in",          today_at(9,  0)),
        (ids["Jane Smith"],    "in",          today_at(9,  2)),
        (ids["Sofia Alvarez"], "in",          today_at(8,  0)),
        (ids["Sofia Alvarez"], "out",         today_at(12, 0)),
        (ids["Priya Raman"],   "in",          today_at(9, 15)),
        (ids["Priya Raman"],   "break_start", today_at(12, 15)),
    ]
    for emp_id, event_type, occurred_at in events:
        conn.execute(
            "INSERT INTO attendance_events "
            "(employee_id, type, occurred_at, note, created_at) "
            "VALUES (?, ?, ?, NULL, ?)",
            (emp_id, event_type, occurred_at, now()),
        )
    conn.commit()

    # Derive shifts for the seeded events
    from app import derive_shift, _refresh_shift
    for emp_id in ids.values():
        evs = [dict(r) for r in conn.execute(
            "SELECT * FROM attendance_events WHERE employee_id = ? "
            "ORDER BY occurred_at",
            (emp_id,),
        ).fetchall()]
        if evs:
            _refresh_shift(conn, emp_id)
    conn.commit()

    n_emp = conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    n_ev = conn.execute("SELECT COUNT(*) FROM attendance_events").fetchone()[0]
    n_sh = conn.execute("SELECT COUNT(*) FROM shifts").fetchone()[0]
    conn.close()
    print("Seeded {} employees, {} events, {} shifts.".format(n_emp, n_ev, n_sh))


if __name__ == "__main__":
    seed()

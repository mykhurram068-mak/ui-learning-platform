"""
Creates hr.db, applies schema.sql, and seeds sample data for Stage 04.
Run once: python seed.py

Seeds:
- 6 employees
- Today's clock events (a realistic morning)
- Two weeks of shifts (so the timesheet and report have data)
- Scheduled shifts for the current week (so the roster comparison works)
"""

from datetime import datetime, timezone, timedelta
from database import init_db, connect


def now():
    return datetime.now(timezone.utc).isoformat()


def today_at(hour, minute=0, days_ago=0):
    now_utc = datetime.now(timezone.utc)
    base = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    base = base - timedelta(days=days_ago)
    return (base + timedelta(hours=hour, minutes=minute)).isoformat()


def date_str(days_ago=0):
    d = datetime.now(timezone.utc).date() - timedelta(days=days_ago)
    return d.isoformat()


def monday_of_current_week():
    today = datetime.now(timezone.utc).date()
    return (today - timedelta(days=today.weekday())).isoformat()


def seed():
    init_db()
    conn = connect()

    # 1. Employees
    employees = [
        ("Jane Smith", "jane@example.com", "manager", 45.00),
        ("Marcus Chen", "marcus@example.com", "employee", 28.00),
        ("Priya Raman", "priya@example.com", "employee", 28.00),
        ("David Wu", "david@example.com", "employee", 30.00),
        ("Sofia Alvarez", "sofia@example.com", "employee", 26.00),
        ("Tariq Khan", "tariq@example.com", "employee", 27.00),
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

    # 2. Today's events (a realistic morning, some still working)
    events_today = [
        (ids["Marcus Chen"], "in", today_at(8, 58)),
        (ids["David Wu"], "in", today_at(9, 0)),
        (ids["Jane Smith"], "in", today_at(9, 2)),
        (ids["Sofia Alvarez"], "in", today_at(8, 0)),
        (ids["Sofia Alvarez"], "out", today_at(12, 0)),
        (ids["Priya Raman"], "in", today_at(9, 15)),
        (ids["Priya Raman"], "break_start", today_at(12, 15)),
    ]
    for emp_id, t, at in events_today:
        conn.execute(
            "INSERT INTO attendance_events "
            "(employee_id, type, occurred_at, note, created_at) "
            "VALUES (?, ?, ?, NULL, ?)",
            (emp_id, t, at, now()),
        )

    # 3. Previous week's events (closed shifts for the timesheet)
    prev_days = [
        # (employee, day_of_week_offset_from_monday, in_h, out_h)
        ("Marcus Chen", 0, 9, 17),
        ("Marcus Chen", 1, 9, 17),
        ("Marcus Chen", 2, 9, 17),
        ("Marcus Chen", 3, 9, 17),
        ("Marcus Chen", 4, 9, 17),
        ("Priya Raman", 0, 9, 17),
        ("Priya Raman", 1, 9, 17),
        ("Priya Raman", 2, 9, 17),
        ("Priya Raman", 3, 9, 17),
        ("David Wu", 0, 8, 18),
        ("David Wu", 1, 8, 18),
        ("David Wu", 2, 8, 18),
        ("David Wu", 3, 8, 18),
        ("David Wu", 4, 8, 18),
        ("Sofia Alvarez", 0, 9, 17),
        ("Sofia Alvarez", 1, 9, 17),
        ("Sofia Alvarez", 2, 9, 17),
        ("Tariq Khan", 0, 9, 17),
        ("Tariq Khan", 1, 9, 17),
    ]
    for name, day_offset, in_h, out_h in prev_days:
        days_ago = 7 + (4 - day_offset)
        emp_id = ids[name]
        conn.execute(
            "INSERT INTO attendance_events "
            "(employee_id, type, occurred_at, note, created_at) "
            "VALUES (?, 'in', ?, NULL, ?)",
            (emp_id, today_at(in_h, 0, days_ago), now()),
        )
        conn.execute(
            "INSERT INTO attendance_events "
            "(employee_id, type, occurred_at, note, created_at) "
            "VALUES (?, 'out', ?, NULL, ?)",
            (emp_id, today_at(out_h, 0, days_ago), now()),
        )

    conn.commit()

    # 4. Derive shifts for all events
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

    # 5. Scheduled shifts for the current week
    monday = monday_of_current_week()
    monday_dt = datetime.fromisoformat(monday + "T00:00:00")
    schedule = [
        ("Jane Smith", 0, 9, 17),
        ("Jane Smith", 1, 9, 17),
        ("Jane Smith", 2, 9, 17),
        ("Jane Smith", 3, 9, 17),
        ("Jane Smith", 4, 9, 17),
        ("Marcus Chen", 0, 9, 17),
        ("Marcus Chen", 1, 9, 17),
        ("Marcus Chen", 2, 9, 17),
        ("Marcus Chen", 3, 9, 17),
        ("Marcus Chen", 4, 9, 17),
        ("Priya Raman", 0, 9, 17),
        ("Priya Raman", 1, 9, 17),
        ("Priya Raman", 2, 9, 17),
        ("Priya Raman", 3, 9, 17),
        ("David Wu", 0, 8, 17),
        ("David Wu", 1, 8, 17),
        ("David Wu", 2, 8, 17),
        ("David Wu", 3, 8, 17),
        ("David Wu", 4, 8, 17),
        ("Sofia Alvarez", 0, 9, 17),
        ("Sofia Alvarez", 1, 9, 17),
        ("Sofia Alvarez", 2, 9, 17),
        ("Tariq Khan", 0, 9, 17),
        ("Tariq Khan", 1, 9, 17),
        ("Tariq Khan", 2, 9, 17),
    ]
    for name, day_offset, in_h, out_h in schedule:
        d = (monday_dt + timedelta(days=day_offset)).date().isoformat()
        start_at = d + "T" + "%02d:00:00+00:00" % in_h
        end_at = d + "T" + "%02d:00:00+00:00" % out_h
        conn.execute(
            "INSERT INTO scheduled_shifts "
            "(employee_id, date, start_at, end_at, note, created_at) "
            "VALUES (?, ?, ?, ?, NULL, ?)",
            (ids[name], d, start_at, end_at, now()),
        )
    conn.commit()

    n_emp = conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    n_ev = conn.execute("SELECT COUNT(*) FROM attendance_events").fetchone()[0]
    n_sh = conn.execute("SELECT COUNT(*) FROM shifts").fetchone()[0]
    n_sched = conn.execute("SELECT COUNT(*) FROM scheduled_shifts").fetchone()[0]
    conn.close()
    print("Seeded {} employees, {} events, {} shifts, {} scheduled.".format(
        n_emp, n_ev, n_sh, n_sched))


if __name__ == "__main__":
    seed()

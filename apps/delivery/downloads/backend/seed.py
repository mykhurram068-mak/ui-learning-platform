"""
Creates delivery.db, applies schema.sql, and seeds sample data.
Run once: python seed.py
"""

from datetime import datetime, timezone, timedelta
from database import init_db, connect


def now():
    return datetime.now(timezone.utc).isoformat()


def minutes_ago(n):
    return (datetime.now(timezone.utc) - timedelta(minutes=n)).isoformat()


def seed():
    init_db()
    conn = connect()

    # 1. Customers
    customers = [
        ("Sarah Johnson", "sarah.j@example.com", "(555) 234-5678", "42 Oak Street, Springfield, IL 62701"),
        ("Michael Chen", "michael.c@example.com", "(555) 345-6789", "18 Elm Avenue, Springfield, IL 62702"),
        ("Priya Raman", "priya.r@example.com", "(555) 456-7890", "207 Pine Road, Springfield, IL 62703"),
        ("David Wu", "david.w@example.com", "(555) 567-8901", "5 Maple Court, Springfield, IL 62704"),
        ("Sofia Alvarez", "sofia.a@example.com", "(555) 678-9012", "88 Birch Lane, Springfield, IL 62705"),
        ("Tariq Khan", "tariq.k@example.com", "(555) 789-0123", "12 Cedar Street, Springfield, IL 62706"),
    ]
    for name, email, phone, address in customers:
        conn.execute(
            "INSERT INTO customers (name, email, phone, address, created_at) VALUES (?, ?, ?, ?, ?)",
            (name, email, phone, address, now()),
        )

    # 2. Couriers
    couriers = [
        ("Alex Rivera", "(555) 100-2000", "car"),
        ("Sam Patel", "(555) 100-2001", "bike"),
        ("Marcus Chen", "(555) 100-2002", "van"),
    ]
    for name, phone, vehicle in couriers:
        conn.execute(
            "INSERT INTO couriers (name, phone, vehicle, status, created_at) VALUES (?, ?, ?, 'available', ?)",
            (name, phone, vehicle, now()),
        )
    conn.commit()

    cust = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM customers")}
    cour = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM couriers")}

    # 3. Deliveries - one per state for demo variety
    deliveries = [
        ("DEL-8F3A2B", cust["Sarah Johnson"], cour["Alex Rivera"], "Central warehouse", "42 Oak Street, Springfield", "out_for_delivery", "express"),
        ("DEL-7C9B14", cust["Michael Chen"], cour["Alex Rivera"], "Central warehouse", "18 Elm Avenue, Springfield", "picked_up", "standard"),
        ("DEL-2E8D91", cust["Priya Raman"], cour["Sam Patel"], "West distribution", "207 Pine Road, Springfield", "in_transit", "standard"),
        ("DEL-6A4F03", cust["David Wu"], cour["Sam Patel"], "Central warehouse", "5 Maple Court, Springfield", "assigned", "standard"),
        ("DEL-9B5E72", cust["Sofia Alvarez"], cour["Marcus Chen"], "Central warehouse", "88 Birch Lane, Springfield", "out_for_delivery", "express"),
        ("DEL-1D3F88", cust["Tariq Khan"], None, "Central warehouse", "12 Cedar Street, Springfield", "pending", "standard"),
    ]
    for code, cust_id, cour_id, origin, dest, status, priority in deliveries:
        conn.execute(
            """INSERT INTO deliveries
               (tracking_code, customer_id, courier_id, origin, destination,
                status, priority, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (code, cust_id, cour_id, origin, dest, status, priority, now(), now()),
        )
    conn.commit()

    deliv = {r["tracking_code"]: r["id"] for r in conn.execute("SELECT id, tracking_code FROM deliveries")}

    # 4. Events for each delivery (chronological, then legs derived from them)
    event_sets = {
        "DEL-8F3A2B": [
            ("assigned", "Assigned to Alex Rivera", minutes_ago(300)),
            ("picked_up", "From Central warehouse", minutes_ago(240)),
            ("in_transit", "Arrived at North facility", minutes_ago(120)),
            ("out_for_delivery", None, minutes_ago(30)),
        ],
        "DEL-7C9B14": [
            ("assigned", "Assigned to Alex Rivera", minutes_ago(280)),
            ("picked_up", "From Central warehouse", minutes_ago(180)),
        ],
        "DEL-2E8D91": [
            ("assigned", "Assigned to Sam Patel", minutes_ago(260)),
            ("picked_up", "From West distribution", minutes_ago(150)),
            ("in_transit", None, minutes_ago(60)),
        ],
        "DEL-6A4F03": [
            ("assigned", "Assigned to Sam Patel", minutes_ago(200)),
        ],
        "DEL-9B5E72": [
            ("assigned", "Assigned to Marcus Chen", minutes_ago(340)),
            ("picked_up", "From Central warehouse", minutes_ago(250)),
            ("in_transit", None, minutes_ago(150)),
            ("out_for_delivery", None, minutes_ago(45)),
        ],
        # DEL-1D3F88 is pending - no events yet
    }

    for code, events in event_sets.items():
        did = deliv[code]
        for etype, note, occurred in events:
            conn.execute(
                """INSERT INTO delivery_events
                   (delivery_id, type, location, note, occurred_at, created_at, created_by)
                   VALUES (?, ?, NULL, ?, ?, ?, 'seed')""",
                (did, etype, note, occurred, occurred),
            )

    conn.commit()

    # 5. Derive legs from events per delivery
    from app import _refresh_current_leg
    for code in event_sets:
        did = deliv[code]
        evs = conn.execute(
            "SELECT type, occurred_at FROM delivery_events WHERE delivery_id = ? ORDER BY occurred_at",
            (did,),
        ).fetchall()
        for ev in evs:
            _refresh_current_leg(conn, did, ev["type"], ev["occurred_at"])
    conn.commit()

    n_cust = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    n_cour = conn.execute("SELECT COUNT(*) FROM couriers").fetchone()[0]
    n_del = conn.execute("SELECT COUNT(*) FROM deliveries").fetchone()[0]
    n_ev = conn.execute("SELECT COUNT(*) FROM delivery_events").fetchone()[0]
    n_leg = conn.execute("SELECT COUNT(*) FROM delivery_legs").fetchone()[0]
    conn.close()
    print("Seeded {} customers, {} couriers, {} deliveries, {} events, {} legs.".format(
        n_cust, n_cour, n_del, n_ev, n_leg))


if __name__ == "__main__":
    seed()

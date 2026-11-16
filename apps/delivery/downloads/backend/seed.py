"""
Creates delivery.db, applies schema.sql, and seeds sample data for Stage 04.
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

    # 3. Deliveries - variety of states including one failed and one delivered
    deliveries = [
        # code, customer, courier, status, priority, minutes_since_creation
        ("DEL-8F3A2B", cust["Sarah Johnson"], cour["Alex Rivera"], "out_for_delivery", "express", 300),
        ("DEL-7C9B14", cust["Michael Chen"], cour["Alex Rivera"], "picked_up", "standard", 280),
        ("DEL-2E8D91", cust["Priya Raman"], cour["Sam Patel"], "in_transit", "standard", 260),
        ("DEL-6A4F03", cust["David Wu"], cour["Sam Patel"], "assigned", "standard", 200),
        ("DEL-9B5E72", cust["Sofia Alvarez"], cour["Marcus Chen"], "out_for_delivery", "express", 340),
        ("DEL-1D3F88", cust["Tariq Khan"], None, "pending", "standard", 100),
        ("DEL-4C7A19", cust["Sarah Johnson"], cour["Marcus Chen"], "delivered", "standard", 480),
        ("DEL-5E2B46", cust["Michael Chen"], cour["Sam Patel"], "failed", "standard", 400),
    ]
    for code, cust_id, cour_id, status, priority, mins in deliveries:
        created = minutes_ago(mins)
        updated = minutes_ago(mins // 2)
        conn.execute(
            """INSERT INTO deliveries
               (tracking_code, customer_id, courier_id, origin, destination,
                status, priority, created_at, updated_at)
               VALUES (?, ?, ?, 'Central warehouse', ?, ?, ?, ?, ?)""",
            (code, cust_id, cour_id,
             "Springfield, IL",
             status, priority, created, updated),
        )
    conn.commit()

    deliv = {r["tracking_code"]: r["id"] for r in conn.execute("SELECT id, tracking_code FROM deliveries")}

    # 4. Events per delivery (chronological)
    event_sets = {
        "DEL-8F3A2B": [
            ("assigned", "Assigned to Alex Rivera", 300),
            ("picked_up", "From Central warehouse", 240),
            ("in_transit", "Arrived at North facility", 120),
            ("out_for_delivery", None, 30),
        ],
        "DEL-7C9B14": [
            ("assigned", "Assigned to Alex Rivera", 280),
            ("picked_up", "From Central warehouse", 180),
        ],
        "DEL-2E8D91": [
            ("assigned", "Assigned to Sam Patel", 260),
            ("picked_up", "From West distribution", 150),
            ("in_transit", None, 60),
        ],
        "DEL-6A4F03": [
            ("assigned", "Assigned to Sam Patel", 200),
        ],
        "DEL-9B5E72": [
            ("assigned", "Assigned to Marcus Chen", 340),
            ("picked_up", "From Central warehouse", 250),
            ("in_transit", None, 150),
            ("out_for_delivery", None, 45),
        ],
        "DEL-4C7A19": [
            ("assigned", "Assigned to Marcus Chen", 480),
            ("picked_up", "From Central warehouse", 420),
            ("in_transit", None, 300),
            ("out_for_delivery", None, 120),
            ("delivered", "Delivered to customer", 60),
        ],
        "DEL-5E2B46": [
            ("assigned", "Assigned to Sam Patel", 400),
            ("picked_up", "From Central warehouse", 340),
            ("failed", "Customer not home", 200),
        ],
    }

    for code, events in event_sets.items():
        did = deliv[code]
        for etype, note, mins in events:
            occurred = minutes_ago(mins)
            conn.execute(
                """INSERT INTO delivery_events
                   (delivery_id, type, location, note, occurred_at, created_at, created_by)
                   VALUES (?, ?, NULL, ?, ?, ?, 'seed')""",
                (did, etype, note, occurred, occurred),
            )

    conn.commit()

    # 5. Derive legs from events
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

    # 6. Proof of delivery for the delivered one
    conn.execute(
        """INSERT INTO proof_of_delivery
           (delivery_id, method, reference, note, captured_at, captured_by)
           VALUES (?, 'signature', 'sig_delivery_4c7a19.svg', 'Signed by Sarah Johnson', ?, 'courier')""",
        (deliv["DEL-4C7A19"], minutes_ago(60)),
    )
    conn.commit()

    # 7. Notifications for any out_for_delivery / delivered / failed
    notify_types = {"out_for_delivery", "delivered", "failed"}
    for code in event_sets:
        did = deliv[code]
        cust_email = conn.execute(
            """SELECT c.email FROM customers c
               JOIN deliveries d ON d.customer_id = c.id
               WHERE d.id = ?""",
            (did,),
        ).fetchone()["email"]
        events = conn.execute(
            "SELECT type, occurred_at FROM delivery_events WHERE delivery_id = ? AND type IN ('out_for_delivery', 'delivered', 'failed')",
            (did,),
        ).fetchall()
        for ev in events:
            conn.execute(
                """INSERT INTO notifications
                   (delivery_id, type, recipient, status, created_at)
                   VALUES (?, ?, ?, 'pending', ?)""",
                (did, ev["type"], cust_email, ev["occurred_at"]),
            )
    conn.commit()

    n_cust = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    n_cour = conn.execute("SELECT COUNT(*) FROM couriers").fetchone()[0]
    n_del = conn.execute("SELECT COUNT(*) FROM deliveries").fetchone()[0]
    n_ev = conn.execute("SELECT COUNT(*) FROM delivery_events").fetchone()[0]
    n_leg = conn.execute("SELECT COUNT(*) FROM delivery_legs").fetchone()[0]
    n_proof = conn.execute("SELECT COUNT(*) FROM proof_of_delivery").fetchone()[0]
    n_notif = conn.execute("SELECT COUNT(*) FROM notifications").fetchone()[0]
    conn.close()
    print("Seeded {} customers, {} couriers, {} deliveries, {} events, {} legs, {} proof, {} notifications.".format(
        n_cust, n_cour, n_del, n_ev, n_leg, n_proof, n_notif))


if __name__ == "__main__":
    seed()

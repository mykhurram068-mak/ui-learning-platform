# Delivery Tracking Backend - Stage 03

Flask + SQLite. Five tables: customers, couriers, deliveries,
delivery_events (append-only), delivery_legs (derived cache).

## Run it

```bash
cd apps/delivery/downloads/backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed.py                      # creates delivery.db with sample data
python app.py                       # http://localhost:5000
```

Then open `http://localhost:5000/` - Flask serves the Stage 03 demo
from `static/delivery-stage-03.html`.

## API

| Method | Path                                | Purpose                                       |
|--------|-------------------------------------|-----------------------------------------------|
| GET    | `/api/state`                        | Deliveries + couriers + recent events         |
| GET    | `/api/deliveries`                   | All deliveries with customer and courier      |
| GET    | `/api/deliveries/active`            | Active deliveries (not delivered/failed/cancelled) |
| GET    | `/api/deliveries/<id>`              | One delivery with events and legs             |
| POST   | `/api/deliveries/<id>/events`       | Record an event (atomic)                      |
| GET    | `/api/couriers`                     | Courier list                                  |
| GET    | `/api/track/<code>`                 | Public tracking (redacted)                    |

## The state machine

```
pending -> assigned -> picked_up -> in_transit -> out_for_delivery -> delivered
```

Plus `failed`, which can fire from `assigned`, `picked_up`, `in_transit`,
or `out_for_delivery`. The server enforces these transitions. Invalid
transitions return 409 with a clear error.

## Atomic event recording

`POST /api/deliveries/<id>/events` does five things in one transaction:

1. Validates the transition against the state machine
2. Inserts the event row
3. Updates the delivery's status and updated_at
4. If `assigned`: sets courier_id and flips courier to `on_delivery`
5. If `delivered`: flips courier back to `available` when they have no more active deliveries
6. Refreshes the current delivery leg (close old, open new if needed)

Any failure rolls back all six.

## Public tracking

`GET /api/track/<code>` returns the tracking code, destination, status,
courier (first name + last initial only), and the event timeline. It
does not return the internal id, customer email, customer phone,
courier phone, or priority. The tracking code is the capability -
anyone with it can view the tracking page.

## Reset

```bash
python seed.py     # drops and recreates delivery.db
```

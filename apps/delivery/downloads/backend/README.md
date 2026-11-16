# Delivery Tracking Backend - Stage 04 (Final)

Flask + SQLite. Seven tables: customers, couriers, deliveries,
delivery_events, delivery_legs, proof_of_delivery, notifications.

## Run it

```bash
cd apps/delivery/downloads/backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed.py                      # creates delivery.db with sample data
python app.py                       # http://localhost:5000
```

Then open `http://localhost:5000/` - Flask serves the Stage 04 demo.

## API

| Method | Path                                | Purpose                                       |
|--------|-------------------------------------|-----------------------------------------------|
| GET    | `/api/state`                        | Deliveries, couriers, recent events           |
| GET    | `/api/deliveries`                   | All deliveries                                |
| GET    | `/api/deliveries/active`            | Active deliveries (for polling)               |
| GET    | `/api/deliveries/<id>`              | One delivery with events, legs, proof         |
| POST   | `/api/deliveries/<id>/events`       | Record an event (atomic)                      |
| POST   | `/api/deliveries/<id>/proof`        | Attach proof of delivery                      |
| POST   | `/api/dispatch/bulk`                | Assign multiple deliveries in one transaction |
| GET    | `/api/couriers`                     | Courier list                                  |
| GET    | `/api/notifications`                | Recent notifications                          |
| GET    | `/api/reports/by-courier?from=&to=` | Deliveries per courier in range               |
| GET    | `/api/reports/delivery-time?from=&to=` | Average delivery time per courier          |
| GET    | `/api/reports/failure-rate?from=&to=` | Failure rate in range                       |
| GET    | `/api/track/<code>`                 | Public tracking (redacted)                    |

## The state machine

```
pending -> assigned -> picked_up -> in_transit -> out_for_delivery -> delivered
```

Plus `failed`, from any assigned-or-later state. Stage 04 adds retry edges:
`failed -> assigned` and `failed -> out_for_delivery` allow a retry without
creating a new delivery.

## Atomic event recording

`POST /api/deliveries/<id>/events` does, in one transaction:

1. Validate the transition against the state machine
2. Insert the event row
3. Update delivery status, updated_at
4. If `assigned`: set courier_id, flip courier to `on_delivery`
5. If `delivered`: flip courier to `available` if they have no more active deliveries
6. Refresh the current leg (close old, open new if needed)
7. Queue a notification if the event is customer-relevant

Any failure rolls back all seven writes.

## Proof of delivery

`POST /api/deliveries/<id>/proof` attaches a proof record. Requires the
delivery to be in `delivered` status. One proof per delivery (UNIQUE
constraint on delivery_id).

Methods: `photo`, `signature`, `otp`. The `reference` field stores the
file path, SVG data URI, or OTP code depending on the method.

## Bulk dispatch

`POST /api/dispatch/bulk` with `{deliveryIds: [...], courierId: N}` assigns
multiple pending deliveries in one transaction. All must be pending. Any
failure rolls back all writes.

## Notifications

When a delivery moves to `out_for_delivery`, `delivered`, or `failed`,
a row is queued in `notifications` with `status='pending'`. Stage 04
never sends - the queue is the contract. A production system would
have a worker that reads pending rows and sends the actual message.

## Reports

Three endpoints, all requiring `from` and `to` (YYYY-MM-DD):

- `/api/reports/by-courier` - delivered, failed, total, failure rate per courier
- `/api/reports/delivery-time` - average minutes from creation to delivered, per courier
- `/api/reports/failure-rate` - overall failure rate in the range

## Reset

```bash
python seed.py     # drops and recreates delivery.db
```

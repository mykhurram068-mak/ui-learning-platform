# HR Attendance Backend - Stage 03

Flask + SQLite. Three tables: employees, attendance_events, shifts.
The events are append-only. The shifts table is derived and upserted
on every event.

## Run it

```bash
cd apps/hr/downloads/backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed.py                      # creates hr.db with sample data
python app.py                       # http://localhost:5000
```

Then open `http://localhost:5000/` - Flask serves the Stage 03 demo
from `static/hr-stage-03.html`.

## API

| Method | Path                  | Purpose                                      |
|--------|-----------------------|----------------------------------------------|
| GET    | `/api/state`          | Everything: employees, today's events, today's shifts |
| GET    | `/api/employees`      | Employee list                                |
| POST   | `/api/clock-in`       | Insert an `in` event (409 if already working) |
| POST   | `/api/clock-out`      | Insert an `out` event (409 if not working)   |
| POST   | `/api/break`          | Insert `break_start` or `break_end` based on current state |

## The derivation

`derive_shift(events, employee_id)` walks events chronologically,
tracks working / on-break / finished, and returns a summary. The
server calls it on every clock-in, clock-out, and break event, then
upserts the shifts row (UNIQUE on employee_id + date).

The client runs the same derivation locally for the live ticking
clock. They agree because they operate on the same events.

## Idempotency

POST /api/clock-in checks whether the employee already has an open
shift (status working or on-break). If so, it returns 409 with the
current shift. The client treats 409 as a no-op and syncs its state.

## Overnight shifts

The shifts.date is the start date (the first event's date). An
employee clocking in at 22:00 Monday and out at 06:00 Tuesday has
a shift on Monday, not Tuesday. The minutes_worked computation uses
the raw timestamps.

## Reset

```bash
python seed.py     # drops and recreates hr.db
```

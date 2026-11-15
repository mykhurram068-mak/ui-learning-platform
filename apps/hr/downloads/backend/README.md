# HR Attendance Backend - Stage 04 (Final)

Flask + SQLite. Four tables: employees, attendance_events (append-only),
shifts (derived cache), scheduled_shifts (the roster plan).

## Run it

```bash
cd apps/hr/downloads/backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed.py                      # creates hr.db with sample data
python app.py                       # http://localhost:5000
```

Then open `http://localhost:5000/` - Flask serves the Stage 04 demo.

## API

| Method | Path                        | Purpose                                       |
|--------|-----------------------------|-----------------------------------------------|
| GET    | `/api/state`                | Full state: employees, today's events, today's shifts |
| GET    | `/api/employees`            | Active employee list                          |
| POST   | `/api/clock-in`             | Insert `in` (409 if already working)          |
| POST   | `/api/clock-out`            | Insert `out` (409 if not working)             |
| POST   | `/api/break`                | Toggle break (409 if not working)             |
| POST   | `/api/correction`           | Insert manual_in/manual_out with a note       |
| GET    | `/api/timesheet?week=`      | Week grid: employees x days x minutes         |
| GET    | `/api/schedule?week=`       | Raw scheduled shifts                          |
| GET    | `/api/roster/compare?week=` | Scheduled vs actual, with late minutes        |
| POST   | `/api/approve-week`         | Flip closed shifts to approved (409 if any open) |
| POST   | `/api/reopen-week`          | Flip approved shifts to closed                |
| GET    | `/api/report?week=`         | Per-employee totals, overtime, late, absent   |

## Overtime

`OVERTIME_THRESHOLD_MINUTES = 40 * 60` at the top of `app.py`. Weekly
threshold. Change it in one place if your jurisdiction differs.

## Manual corrections

Corrections are new `manual_in` or `manual_out` events with a note.
They never edit existing events. The derivation handles both types
identically. A correction on an approved week returns 409 - reopen
the week first.

## Approval workflow

`POST /api/approve-week` with `{weekStart: "YYYY-MM-DD"}` flips every
closed shift in the week to approved. It returns 409 if any shift in
the week is still open. `POST /api/reopen-week` reverts approved
shifts back to closed so a correction can be made.

## Reset

```bash
python seed.py     # drops and recreates hr.db
```

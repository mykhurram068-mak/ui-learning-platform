-- HR Attendance schema - Stage 04 (final)
-- Four tables: employees, attendance_events (append-only),
-- shifts (derived cache), scheduled_shifts (the roster plan).

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS shifts;
DROP TABLE IF EXISTS scheduled_shifts;
DROP TABLE IF EXISTS attendance_events;
DROP TABLE IF EXISTS employees;

CREATE TABLE employees (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  name        TEXT NOT NULL,
  email       TEXT NOT NULL UNIQUE,
  role        TEXT NOT NULL DEFAULT 'employee'
              CHECK (role IN ('employee', 'manager')),
  hourly_rate REAL NOT NULL DEFAULT 0 CHECK (hourly_rate >= 0),
  hired_at    TEXT NOT NULL,
  archived_at TEXT
);

CREATE TABLE attendance_events (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id INTEGER NOT NULL,
  type        TEXT NOT NULL
              CHECK (type IN ('in', 'out', 'break_start', 'break_end',
                              'manual_in', 'manual_out')),
  occurred_at TEXT NOT NULL,
  note        TEXT,
  created_at  TEXT NOT NULL,
  FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE RESTRICT
);

CREATE TABLE shifts (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id    INTEGER NOT NULL,
  date           TEXT NOT NULL,
  clock_in_at    TEXT,
  clock_out_at   TEXT,
  break_minutes  INTEGER NOT NULL DEFAULT 0,
  minutes_worked INTEGER NOT NULL DEFAULT 0,
  status         TEXT NOT NULL DEFAULT 'open'
                 CHECK (status IN ('open', 'closed', 'approved')),
  created_at     TEXT NOT NULL,
  UNIQUE (employee_id, date),
  FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE RESTRICT
);

CREATE TABLE scheduled_shifts (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id INTEGER NOT NULL,
  date        TEXT NOT NULL,
  start_at    TEXT NOT NULL,
  end_at      TEXT NOT NULL,
  note        TEXT,
  created_at  TEXT NOT NULL,
  UNIQUE (employee_id, date, start_at),
  FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE RESTRICT
);

CREATE INDEX idx_events_employee   ON attendance_events(employee_id);
CREATE INDEX idx_events_occurred   ON attendance_events(occurred_at);
CREATE INDEX idx_shifts_date       ON shifts(date);
CREATE INDEX idx_shifts_employee   ON shifts(employee_id);
CREATE INDEX idx_sched_date        ON scheduled_shifts(date);
CREATE INDEX idx_sched_employee    ON scheduled_shifts(employee_id);

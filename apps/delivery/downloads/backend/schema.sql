-- Delivery Tracking schema - Stage 03
-- Five tables: customers, couriers, deliveries, delivery_events, delivery_legs.

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS delivery_legs;
DROP TABLE IF EXISTS delivery_events;
DROP TABLE IF EXISTS deliveries;
DROP TABLE IF EXISTS couriers;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  name       TEXT NOT NULL,
  email      TEXT NOT NULL UNIQUE,
  phone      TEXT,
  address    TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE couriers (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  name       TEXT NOT NULL,
  phone      TEXT,
  vehicle    TEXT NOT NULL DEFAULT 'van'
             CHECK (vehicle IN ('bike', 'car', 'van')),
  status     TEXT NOT NULL DEFAULT 'available'
             CHECK (status IN ('available', 'on_delivery', 'off_duty')),
  created_at TEXT NOT NULL
);

CREATE TABLE deliveries (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  tracking_code TEXT NOT NULL UNIQUE,
  customer_id   INTEGER NOT NULL,
  courier_id    INTEGER,
  origin        TEXT NOT NULL,
  destination   TEXT NOT NULL,
  status        TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'assigned', 'picked_up',
                                  'in_transit', 'out_for_delivery',
                                  'delivered', 'failed', 'cancelled')),
  priority      TEXT NOT NULL DEFAULT 'standard'
                CHECK (priority IN ('standard', 'express')),
  created_at    TEXT NOT NULL,
  updated_at    TEXT NOT NULL,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE RESTRICT,
  FOREIGN KEY (courier_id)  REFERENCES couriers(id)  ON DELETE SET NULL
);

CREATE TABLE delivery_events (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  delivery_id INTEGER NOT NULL,
  type        TEXT NOT NULL
              CHECK (type IN ('assigned', 'picked_up', 'in_transit',
                              'out_for_delivery', 'delivered', 'failed',
                              'note')),
  location    TEXT,
  note        TEXT,
  occurred_at TEXT NOT NULL,
  created_at  TEXT NOT NULL,
  created_by  TEXT NOT NULL DEFAULT 'api',
  FOREIGN KEY (delivery_id) REFERENCES deliveries(id) ON DELETE CASCADE
);

CREATE TABLE delivery_legs (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  delivery_id   INTEGER NOT NULL,
  leg_index     INTEGER NOT NULL,
  from_location TEXT,
  to_location   TEXT,
  started_at    TEXT NOT NULL,
  ended_at      TEXT,
  status        TEXT NOT NULL DEFAULT 'active'
                CHECK (status IN ('active', 'completed', 'failed')),
  FOREIGN KEY (delivery_id) REFERENCES deliveries(id) ON DELETE CASCADE
);

CREATE INDEX idx_deliveries_code     ON deliveries(tracking_code);
CREATE INDEX idx_deliveries_status   ON deliveries(status);
CREATE INDEX idx_deliveries_courier  ON deliveries(courier_id);
CREATE INDEX idx_events_delivery     ON delivery_events(delivery_id);
CREATE INDEX idx_events_occurred     ON delivery_events(occurred_at);
CREATE INDEX idx_legs_delivery       ON delivery_legs(delivery_id);
CREATE INDEX idx_legs_active         ON delivery_legs(delivery_id, ended_at);

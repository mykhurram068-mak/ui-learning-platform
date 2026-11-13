-- Two tables, one foreign key.
-- products.supplier_id -> suppliers.id

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS suppliers;

CREATE TABLE suppliers (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  name       TEXT NOT NULL UNIQUE,
  email      TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE products (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  sku           TEXT NOT NULL UNIQUE,          -- the Stage 02 client rule, enforced here
  name          TEXT NOT NULL,
  category      TEXT NOT NULL DEFAULT 'Uncategorized',
  price         REAL NOT NULL CHECK (price >= 0),
  cost          REAL NOT NULL CHECK (cost >= 0),
  quantity      INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
  reorder_level INTEGER NOT NULL DEFAULT 10 CHECK (reorder_level >= 0),
  supplier_id   INTEGER,
  created_at    TEXT NOT NULL,
  updated_at    TEXT NOT NULL,
  FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
);

CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_supplier ON products(supplier_id);

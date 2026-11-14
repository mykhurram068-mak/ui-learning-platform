-- POS tables: sales, sale_lines, payments.
-- Plus defensive definitions of the shared inventory tables
-- (products, stock_movements) so the seed script works
-- even if the inventory app hasn't been built yet.
--
-- If inventory.db already exists with these tables, the
-- IF NOT EXISTS clauses below are no-ops. If it doesn't,
-- they create a minimal inventory schema the POS can
-- read from and write stock movements into.

PRAGMA foreign_keys = ON;

-- ─── Shared inventory tables (no-op if they exist) ───
CREATE TABLE IF NOT EXISTS products (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  sku           TEXT NOT NULL UNIQUE,
  name          TEXT NOT NULL,
  category      TEXT NOT NULL DEFAULT 'Uncategorized',
  price         REAL NOT NULL CHECK (price >= 0),
  cost          REAL NOT NULL CHECK (cost >= 0),
  quantity      INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
  reorder_level INTEGER NOT NULL DEFAULT 10 CHECK (reorder_level >= 0),
  supplier_id   INTEGER,
  created_at    TEXT NOT NULL,
  updated_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stock_movements (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  product_id INTEGER NOT NULL,
  delta      INTEGER NOT NULL,
  reason     TEXT NOT NULL,
  note       TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- ─── POS tables ───
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS sale_lines;
DROP TABLE IF EXISTS sales;

CREATE TABLE sales (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  cashier        TEXT NOT NULL DEFAULT 'Alex Rivera',
  subtotal       REAL NOT NULL CHECK (subtotal >= 0),
  tax_rate       REAL NOT NULL CHECK (tax_rate >= 0),
  tax_total      REAL NOT NULL CHECK (tax_total >= 0),
  grand_total    REAL NOT NULL CHECK (grand_total >= 0),
  status         TEXT NOT NULL DEFAULT 'paid'
                 CHECK (status IN ('open', 'paid', 'voided', 'held')),
  created_at     TEXT NOT NULL,
  paid_at        TEXT
);

CREATE TABLE sale_lines (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  sale_id     INTEGER NOT NULL,
  product_id  INTEGER NOT NULL,
  product_name TEXT NOT NULL,          -- snapshot at sale time
  qty         INTEGER NOT NULL CHECK (qty > 0),
  unit_price  REAL NOT NULL CHECK (unit_price >= 0),   -- snapshot
  line_total  REAL NOT NULL CHECK (line_total >= 0),   -- snapshot
  created_at  TEXT NOT NULL,
  FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
);

CREATE TABLE payments (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  sale_id    INTEGER NOT NULL,
  method     TEXT NOT NULL CHECK (method IN ('cash', 'card', 'other')),
  amount     REAL NOT NULL CHECK (amount >= 0),
  tendered   REAL NOT NULL DEFAULT 0 CHECK (tendered >= 0),
  change     REAL NOT NULL DEFAULT 0 CHECK (change >= 0),
  created_at TEXT NOT NULL,
  FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE
);

CREATE INDEX idx_sales_created    ON sales(created_at);
CREATE INDEX idx_sales_status     ON sales(status);
CREATE INDEX idx_lines_sale       ON sale_lines(sale_id);
CREATE INDEX idx_lines_product    ON sale_lines(product_id);
CREATE INDEX idx_payments_sale    ON payments(sale_id);

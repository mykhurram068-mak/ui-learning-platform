# POS Backend — Stage 04 (Final)

Flask + SQLite. Three POS tables (`sales`, `sale_lines`, `payments`).
Shares `products` + `stock_movements` with the Inventory app.

## Prerequisite

The POS reads `products` from the shared `inventory.db`. If you
built Inventory Stage 04, `inventory.db` exists — `seed.py`
leaves its products alone. If not, `seed.py` creates a minimal
inventory schema and 8 sample products.

## Run it

```bash
cd apps/pos/downloads/backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed.py                      # creates OR migrates inventory.db
python app.py                       # http://localhost:5000
```

`seed.py` is idempotent: on a fresh install it creates everything;
on an existing Stage 03 database it applies `ALTER TABLE`
migrations (adds `sales.refund_of_sale_id` and
`products.archived_at`) without dropping data.

Then open `http://localhost:5000/` — Flask serves the Stage 04
demo from `static/pos-stage-04.html`.

## API

| Method | Path                              | Purpose                                       |
|--------|-----------------------------------|-----------------------------------------------|
| GET    | `/api/products`                   | Catalog (in-stock, non-archived)              |
| GET    | `/api/categories`                 | Distinct categories for filter chips          |
| POST   | `/api/sales`                      | **Atomic checkout** — creates a full sale     |
| GET    | `/api/sales`                      | History — `?from=&to=&method=&cashier=&status=` |
| GET    | `/api/sales/<id>`                 | One sale with lines + payment (receipt)       |
| POST   | `/api/sales/<id>/refund`          | Create a reversal sale (original untouched)   |
| POST   | `/api/sales/hold`                 | Park a cart (`status='held'`)                 |
| GET    | `/api/sales/held`                 | List held carts                               |
| POST   | `/api/sales/<id>/resume`          | Load a held cart's lines                      |
| POST   | `/api/sales/<id>/void`            | Delete a held cart                            |
| GET    | `/api/reports/z?date=YYYY-MM-DD`  | End-of-day reconciliation report              |
| POST   | `/api/products/<id>/archive`      | Hide from catalog (do not delete — RESTRICT)  |
| POST   | `/api/products/<id>/unarchive`    | Restore to catalog                            |

## The atomic checkout

`POST /api/sales` writes to five tables in one transaction:
`sales`, `sale_lines`, `payments`, `stock_movements`, `products.quantity`.
Any failure rolls back all five.

## Refunds as reversal sales

A refund does NOT delete the original sale. It creates a **new
sale** with:
- negative line quantities and totals
- `refund_of_sale_id` pointing at the original
- a negative payment row
- positive `stock_movements` rows (`reason='refunded'`)

The original stays immutable. This is how accounting works.

## The Z-report

`GET /api/reports/z?date=2026-11-14` returns gross sales, refunds,
net sales, tax collected, breakdown by payment method, and a
`reconciles` boolean. If `reconciles` is false, the sum of payments
does not equal net sales — someone's till is short.

## Schema notes

- **`sale_lines.product_id` uses `ON DELETE RESTRICT`.** Sold
  products cannot be deleted. They can be archived.
- **`sale_lines.unit_price` and `product_name` are snapshots.**
  Historical receipts never change when the catalog does.
- **`sale_lines.qty` and `payments.amount` can be negative.**
  That's what a refund is.

## Reset

```bash
python seed.py     # safe on any state — migrates or seeds as needed
```

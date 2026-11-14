# POS Backend — Stage 03

Flask + SQLite backend for the POS app. Three POS tables (`sales`,
`sale_lines`, `payments`) that share the products + stock_movements
tables with the Inventory app.

## Prerequisite

The POS reads `products` from the Inventory database. If you have
already built Inventory Stage 04, `inventory.db` exists — the POS
seed script leaves its `products` and `stock_movements` alone.

If not, `seed.py` creates `inventory.db` with a minimal inventory
schema and 8 sample products. The POS works standalone either way.

## Run it

```bash
cd apps/pos/downloads/backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed.py                      # creates inventory.db + seeds sample data
python app.py                       # http://localhost:5000
```

Then open `http://localhost:5000/` — Flask serves the Stage 03 demo
from `static/pos-stage-03.html`.

## API

| Method | Path                    | Purpose                                     |
|--------|-------------------------|---------------------------------------------|
| GET    | `/api/products`         | Catalog (in-stock only; `?all=1` for all)   |
| GET    | `/api/categories`       | Distinct categories for filter chips        |
| POST   | `/api/sales`            | **Atomic checkout** — creates a full sale   |
| GET    | `/api/sales`            | Recent sales (`?limit=20`)                  |
| GET    | `/api/sales/<id>`       | One sale with lines + payment (receipt)     |

## The atomic checkout

`POST /api/sales` writes to five tables in one transaction:

1. `sales` — one row
2. `sale_lines` — one row per cart line (with price snapshot)
3. `payments` — one row
4. `stock_movements` — one row per line (`reason='sold'`, negative delta)
5. `products.quantity` — decremented per line

If any step fails — product not found, stock insufficient, cash
short, anything — the whole transaction rolls back. No half-sales.

## Schema decisions worth knowing

- **`sale_lines.product_id` uses `ON DELETE RESTRICT`.** You cannot
  delete a product that has been sold. Products can be archived
  (Stage 04) but not deleted.
- **`sale_lines.unit_price` and `sale_lines.product_name` are
  snapshots.** Changing a product's price or name tomorrow does not
  rewrite yesterday's receipts.
- **`payments.tendered` and `payments.change`** store what the
  customer handed over and what came back (cash sales). Card sales
  store `tendered == amount`, `change == 0`.

## Reset

```bash
python seed.py     # drops POS tables, keeps inventory products if they exist
```

# Inventory Backend — Stage 03

Flask + SQLite API for the inventory app.

## Run it

```bash
cd apps/inventory/downloads/backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed.py                      # creates inventory.db with sample data
python app.py                       # http://localhost:5000
```

Then open `http://localhost:5000/` — it serves the Stage 03 demo HTML
from `static/inventory-stage-03.html`.

## API

| Method | Path                    | Purpose                         |
|--------|-------------------------|---------------------------------|
| GET    | `/api/products`         | List products (`?q=`, `?category=`) |
| GET    | `/api/products/<id>`    | Single product                  |
| POST   | `/api/products`         | Create (409 if SKU exists)      |
| PUT    | `/api/products/<id>`    | Update (409 if SKU exists)      |
| DELETE | `/api/products/<id>`    | Delete                          |
| GET    | `/api/suppliers`        | Supplier list for dropdown      |
| GET    | `/api/categories`       | Distinct categories             |

## Data model

- `suppliers` — id, name (unique), email, created_at
- `products` — id, sku (unique), name, category, price, cost, quantity,
  reorder_level, supplier_id (FK -> suppliers.id, ON DELETE SET NULL),
  created_at, updated_at

## The SKU rule, twice

The client checks duplicate SKUs before saving (Stage 02 logic).
The server **also** checks, and the schema has `UNIQUE` on `sku`.
That's the "never trust the client" boundary — the client check is UX,
the schema is integrity.

## Reset

```bash
python seed.py     # wipes inventory.db and reseeds
```

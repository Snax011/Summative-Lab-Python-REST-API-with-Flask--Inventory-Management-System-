# Inventory Management System

A Flask REST API and command-line client for managing retail inventory. Storage is intentionally in memory, so restarting the server resets the sample data.

## Setup

```bash
cd inventory-management-system
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

In another terminal, with the environment activated, run `python cli.py`. The CLI can list, view, add, update, delete, and find/import products.

## API Routes

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/inventory` | List inventory items. |
| GET | `/inventory/<id>` | Get one item. |
| POST | `/inventory` | Create an item with `name`, `price`, and `stock`. |
| PATCH | `/inventory/<id>` | Update any editable item fields. |
| DELETE | `/inventory/<id>` | Delete an item. |
| GET | `/product-lookup?barcode=<barcode>` | Look up OpenFoodFacts product data. |
| GET | `/product-lookup?name=<name>` | Search OpenFoodFacts by name. |
| POST | `/inventory/import` | Look up and add a product; include `barcode` or `name`, plus `price` and `stock`. |

Example create request:

```bash
curl -X POST http://127.0.0.1:5000/inventory -H 'Content-Type: application/json' -d '{"name":"Oat Milk","price":3.50,"stock":12}'
```

The external integration uses the current OpenFoodFacts v2 product endpoint. Tests mock `requests.get`, so they run predictably without network access:

```bash
pytest -q
```
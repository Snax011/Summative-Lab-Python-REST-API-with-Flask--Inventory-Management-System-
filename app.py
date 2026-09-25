"""Flask REST API for the inventory management system."""

from itertools import count

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
inventory = [{"id": 1, "name": "Organic Almond Milk", "brand": "Silk", "ingredients": "Filtered water, almonds, cane sugar", "price": 4.99, "stock": 18, "barcode": "00036632071123"}]
next_id = count(2)
REQUIRED_FIELDS = {"name", "price", "stock"}
EDITABLE_FIELDS = {"name", "brand", "ingredients", "price", "stock", "barcode"}


def find_item(item_id):
    return next((item for item in inventory if item["id"] == item_id), None)


def validate_item(data, require_all=True):
    if not isinstance(data, dict):
        return "JSON request body is required"
    missing_fields = REQUIRED_FIELDS - data.keys() if require_all else set()
    if missing_fields:
        return f"Missing required fields: {', '.join(sorted(missing_fields))}"
    if not require_all and not (EDITABLE_FIELDS & data.keys()):
        return "Provide at least one editable field"
    if "price" in data and (not isinstance(data["price"], (int, float)) or data["price"] < 0):
        return "price must be a non-negative number"
    if "stock" in data and (not isinstance(data["stock"], int) or data["stock"] < 0):
        return "stock must be a non-negative integer"
    return None


def normalize_product(product, barcode=None):
    return {"name": product.get("product_name") or product.get("product_name_en") or "Unnamed product", "brand": product.get("brands", ""), "ingredients": product.get("ingredients_text", ""), "barcode": barcode or product.get("code", "")}


def fetch_open_food_facts(barcode=None, name=None):
    try:
        if barcode:
            response = requests.get(f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json", timeout=10, headers={"User-Agent": "InventoryManagementSystem/1.0"})
            response.raise_for_status()
            payload = response.json()
            return normalize_product(payload.get("product", {}), barcode) if payload.get("status") == 1 else None
        response = requests.get("https://world.openfoodfacts.org/api/v2/search", params={"search_terms": name, "page_size": 1, "fields": "product_name,brands,ingredients_text,code"}, timeout=10, headers={"User-Agent": "InventoryManagementSystem/1.0"})
        response.raise_for_status()
        products = response.json().get("products", [])
        return normalize_product(products[0]) if products else None
    except (requests.RequestException, ValueError):
        return None


@app.get("/")
def home():
    return jsonify({"message": "Inventory Management API"})


@app.get("/inventory")
def get_inventory():
    return jsonify(inventory)


@app.get("/inventory/<int:item_id>")
def get_inventory_item(item_id):
    item = find_item(item_id)
    return (jsonify(item), 200) if item else (jsonify({"error": "Inventory item not found"}), 404)


@app.post("/inventory")
def create_inventory_item():
    data = request.get_json(silent=True)
    error = validate_item(data)
    if error:
        return jsonify({"error": error}), 400
    item = {"id": next(next_id), **{field: data.get(field, "") for field in EDITABLE_FIELDS}}
    inventory.append(item)
    return jsonify(item), 201


@app.patch("/inventory/<int:item_id>")
def update_inventory_item(item_id):
    item = find_item(item_id)
    if item is None:
        return jsonify({"error": "Inventory item not found"}), 404
    data = request.get_json(silent=True)
    error = validate_item(data, require_all=False)
    if error:
        return jsonify({"error": error}), 400
    item.update({field: value for field, value in data.items() if field in EDITABLE_FIELDS})
    return jsonify(item)


@app.delete("/inventory/<int:item_id>")
def delete_inventory_item(item_id):
    item = find_item(item_id)
    if item is None:
        return jsonify({"error": "Inventory item not found"}), 404
    inventory.remove(item)
    return "", 204


@app.get("/product-lookup")
def product_lookup():
    barcode, name = request.args.get("barcode"), request.args.get("name")
    if not barcode and not name:
        return jsonify({"error": "Provide a barcode or name query parameter"}), 400
    product = fetch_open_food_facts(barcode=barcode, name=name)
    return (jsonify(product), 200) if product else (jsonify({"error": "Product was not found or the external API is unavailable"}), 404)


@app.post("/inventory/import")
def import_inventory_item():
    data = request.get_json(silent=True) or {}
    product = fetch_open_food_facts(barcode=data.get("barcode"), name=data.get("name"))
    if product is None:
        return jsonify({"error": "Product was not found or the external API is unavailable"}), 404
    item = {"id": next(next_id), **product, "price": data.get("price", 0), "stock": data.get("stock", 0)}
    error = validate_item(item)
    if error:
        return jsonify({"error": error}), 400
    inventory.append(item)
    return jsonify(item), 201


if __name__ == "__main__":
    app.run(debug=True)
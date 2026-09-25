from unittest.mock import Mock, patch

import pytest
import app as inventory_app


@pytest.fixture(autouse=True)
def reset_inventory():
    inventory_app.inventory[:] = [{"id": 1, "name": "Organic Almond Milk", "brand": "Silk", "ingredients": "Filtered water, almonds, cane sugar", "price": 4.99, "stock": 18, "barcode": "00036632071123"}]


@pytest.fixture
def client():
    inventory_app.app.config["TESTING"] = True
    return inventory_app.app.test_client()


def test_get_inventory_and_single_item(client):
    assert client.get("/inventory").status_code == 200
    response = client.get("/inventory/1")
    assert response.status_code == 200
    assert response.json["name"] == "Organic Almond Milk"


def test_create_update_and_delete_item(client):
    created = client.post("/inventory", json={"name": "Oat Milk", "price": 3.5, "stock": 9})
    assert created.status_code == 201
    item_id = created.json["id"]
    assert client.patch(f"/inventory/{item_id}", json={"stock": 12}).json["stock"] == 12
    assert client.delete(f"/inventory/{item_id}").status_code == 204
    assert client.get(f"/inventory/{item_id}").status_code == 404


def test_create_rejects_invalid_data(client):
    response = client.post("/inventory", json={"name": "Oat Milk", "price": -1, "stock": 2})
    assert response.status_code == 400
    assert "non-negative" in response.json["error"]


@patch("app.requests.get")
def test_lookup_and_import_external_product(mock_get, client):
    mock_response = Mock()
    mock_response.json.return_value = {"status": 1, "product": {"product_name": "Sparkling Water", "brands": "Clear Spring", "ingredients_text": "Water"}}
    mock_get.return_value = mock_response
    lookup = client.get("/product-lookup?barcode=123")
    assert lookup.status_code == 200
    assert lookup.json["name"] == "Sparkling Water"
    imported = client.post("/inventory/import", json={"barcode": "123", "price": 1.25, "stock": 6})
    assert imported.status_code == 201
    assert imported.json["barcode"] == "123"
    assert mock_get.call_count == 2
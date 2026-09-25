"""Interactive CLI client for the inventory API."""

import json
import requests

BASE_URL = "http://127.0.0.1:5000"


def request_api(method, path, payload=None):
    try:
        response = requests.request(method, f"{BASE_URL}{path}", json=payload, timeout=10)
        print("Item deleted." if response.status_code == 204 else json.dumps(response.json(), indent=2))
    except requests.RequestException as error:
        print(f"API request failed: {error}")
    except ValueError:
        print("The API returned an invalid response.")


def item_input(include_name=True):
    item = {"name": input("Name: ").strip()} if include_name else {}
    for field, converter in (("price", float), ("stock", int)):
        value = input(f"{field.title()}: ").strip()
        if value:
            try:
                item[field] = converter(value)
            except ValueError:
                print(f"{field.title()} must be numeric.")
                return None
    return item


def main():
    while True:
        print("\n1: List | 2: View | 3: Add | 4: Update | 5: Delete | 6: Find/import | 0: Exit")
        choice = input("Choose an action: ").strip()
        if choice == "0":
            return
        if choice == "1":
            request_api("GET", "/inventory")
        elif choice in {"2", "5"}:
            item_id = input("Item ID: ").strip()
            request_api("GET" if choice == "2" else "DELETE", f"/inventory/{item_id}")
        elif choice in {"3", "4"}:
            path = "/inventory" if choice == "3" else f"/inventory/{input('Item ID: ').strip()}"
            payload = item_input(include_name=choice == "3")
            if payload is not None:
                request_api("POST" if choice == "3" else "PATCH", path, payload)
        elif choice == "6":
            barcode = input("Barcode (blank searches by name): ").strip()
            payload = {"barcode": barcode} if barcode else {"name": input("Product name: ").strip()}
            payload.update(item_input(include_name=False) or {})
            request_api("POST", "/inventory/import", payload)
        else:
            print("Choose a listed action.")


if __name__ == "__main__":
    main()
def _create_product(client, auth_headers, sku="SALE-SKU", price=10.0, stock=10, tax=0):
    resp = client.post("/api/v1/products", json={
        "sku": sku, "name": "Sale Product", "price": price, "cost_price": 4.0,
        "tax_rate": tax, "initial_stock": stock, "low_stock_threshold": 1,
    }, headers=auth_headers)
    return resp.get_json()["data"]


def test_full_checkout_flow(client, auth_headers):
    product = _create_product(client, auth_headers, stock=10)

    resp = client.post("/api/v1/sales", json={
        "items": [{"product_id": product["id"], "quantity": 2}],
        "payments": [{"method": "cash", "amount": 20.0, "amount_tendered": 20.0}],
    }, headers=auth_headers)

    assert resp.status_code == 201
    sale = resp.get_json()["data"]
    assert sale["total_amount"] == 20.0
    assert sale["status"] == "completed"

    # Stock should be deducted.
    inv_resp = client.get(f"/api/v1/inventory/product/{product['id']}", headers=auth_headers)
    assert inv_resp.get_json()["data"]["quantity"] == 8


def test_checkout_insufficient_stock(client, auth_headers):
    product = _create_product(client, auth_headers, stock=1)
    resp = client.post("/api/v1/sales", json={
        "items": [{"product_id": product["id"], "quantity": 5}],
        "payments": [{"method": "cash", "amount": 50.0, "amount_tendered": 50.0}],
    }, headers=auth_headers)
    assert resp.status_code == 409


def test_void_sale_restores_stock(client, auth_headers):
    product = _create_product(client, auth_headers, stock=10)
    sale_resp = client.post("/api/v1/sales", json={
        "items": [{"product_id": product["id"], "quantity": 3}],
        "payments": [{"method": "cash", "amount": 30.0, "amount_tendered": 30.0}],
    }, headers=auth_headers)
    sale_id = sale_resp.get_json()["data"]["id"]

    void_resp = client.post(f"/api/v1/sales/{sale_id}/void", json={"reason": "test"}, headers=auth_headers)
    assert void_resp.status_code == 200
    assert void_resp.get_json()["data"]["status"] == "voided"

    inv_resp = client.get(f"/api/v1/inventory/product/{product['id']}", headers=auth_headers)
    assert inv_resp.get_json()["data"]["quantity"] == 10

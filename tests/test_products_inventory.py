def _create_product(client, auth_headers, sku="SKU001", stock=10):
    resp = client.post("/api/v1/products", json={
        "sku": sku, "name": "Test Product", "price": 9.99, "cost_price": 5.0,
        "tax_rate": 10, "initial_stock": stock, "low_stock_threshold": 2,
    }, headers=auth_headers)
    return resp


def test_create_product(client, auth_headers):
    resp = _create_product(client, auth_headers)
    assert resp.status_code == 201
    data = resp.get_json()["data"]
    assert data["sku"] == "SKU001"
    assert data["current_stock"] == 10


def test_duplicate_sku_rejected(client, auth_headers):
    _create_product(client, auth_headers, sku="SKU002")
    resp = _create_product(client, auth_headers, sku="SKU002")
    assert resp.status_code == 409


def test_inventory_restock(client, auth_headers):
    create_resp = _create_product(client, auth_headers, sku="SKU003", stock=5)
    product_id = create_resp.get_json()["data"]["id"]

    resp = client.post(f"/api/v1/inventory/product/{product_id}/restock",
                        json={"quantity": 20, "reason": "New shipment"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.get_json()["data"]["quantity"] == 25


def test_low_stock_listing(client, auth_headers):
    _create_product(client, auth_headers, sku="SKU004", stock=1)
    resp = client.get("/api/v1/inventory/low-stock", headers=auth_headers)
    assert resp.status_code == 200
    skus = [i["product_name"] for i in resp.get_json()["data"]]
    assert len(skus) >= 1

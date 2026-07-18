def _create_product(client, auth_headers, sku="V3-SKU", stock=10):
    resp = client.post("/api/v1/products", json={
        "sku": sku, "name": "V3 Product", "price": 10.0, "cost_price": 4.0,
        "tax_rate": 0, "initial_stock": stock, "low_stock_threshold": 2,
    }, headers=auth_headers)
    return resp.get_json()["data"]


def test_unauthenticated_register_is_rejected(client):
    """Critical security fix: /auth/register must require auth + users.manage now."""
    resp = client.post("/api/v1/auth/register", json={
        "username": "sneaky", "full_name": "Sneaky Admin", "password": "secret123", "role_name": "admin",
    })
    assert resp.status_code == 401


def test_openapi_has_bearer_security_scheme(client):
    resp = client.get("/openapi.json")
    spec = resp.get_json()
    assert "bearerAuth" in spec["components"]["securitySchemes"]
    assert spec["security"] == [{"bearerAuth": []}]
    # Login must override to public.
    assert spec["paths"]["/api/v1/auth/login"]["post"].get("security") == []


def test_gift_card_issue_and_redeem(client, auth_headers):
    resp = client.post("/api/v1/gift-cards", json={"initial_value": 50.0}, headers=auth_headers)
    assert resp.status_code == 201
    card = resp.get_json()["data"]
    assert card["balance"] == 50.0

    resp = client.get(f"/api/v1/gift-cards/{card['code']}/balance", headers=auth_headers)
    assert resp.get_json()["data"]["balance"] == 50.0

    resp = client.post(f"/api/v1/gift-cards/{card['code']}/redeem", json={"amount": 20.0}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.get_json()["data"]["balance"] == 30.0

    resp = client.post(f"/api/v1/gift-cards/{card['code']}/redeem", json={"amount": 999.0}, headers=auth_headers)
    assert resp.status_code == 409


def test_gift_card_as_sale_payment_method(client, auth_headers):
    product = _create_product(client, auth_headers, sku="GC-PAY", stock=5)
    card_resp = client.post("/api/v1/gift-cards", json={"initial_value": 100.0}, headers=auth_headers)
    code = card_resp.get_json()["data"]["code"]

    resp = client.post("/api/v1/sales", json={
        "items": [{"product_id": product["id"], "quantity": 2}],
        "payments": [{"method": "gift_card", "amount": 20.0, "gift_card_code": code}],
    }, headers=auth_headers)
    assert resp.status_code == 201

    balance_resp = client.get(f"/api/v1/gift-cards/{code}/balance", headers=auth_headers)
    assert balance_resp.get_json()["data"]["balance"] == 80.0


def test_favorites_pin_unpin(client, auth_headers):
    product = _create_product(client, auth_headers, sku="FAV-SKU")
    resp = client.post(f"/api/v1/favorites/{product['id']}", headers=auth_headers)
    assert resp.status_code == 201

    resp = client.get("/api/v1/favorites", headers=auth_headers)
    assert len(resp.get_json()["data"]) == 1

    resp = client.delete(f"/api/v1/favorites/{product['id']}", headers=auth_headers)
    assert resp.status_code == 200
    resp = client.get("/api/v1/favorites", headers=auth_headers)
    assert len(resp.get_json()["data"]) == 0


def test_global_search(client, auth_headers):
    _create_product(client, auth_headers, sku="SEARCHABLE-SKU")
    resp = client.get("/api/v1/search?q=SEARCHABLE", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["total_count"] >= 1
    assert any(p["sku"] == "SEARCHABLE-SKU" for p in data["products"])


def test_receipt_and_label_templates(client, auth_headers):
    resp = client.post("/api/v1/templates/receipts", json={
        "name": "Default 80mm", "paper_width_mm": 80,
        "layout": {"elements": [{"type": "logo"}, {"type": "items_table"}, {"type": "qr_code"}]},
        "set_default": True,
    }, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.get_json()["data"]["is_default"] is True

    resp = client.post("/api/v1/templates/labels", json={
        "name": "Small Label", "label_size": "small", "layout": {"elements": [{"type": "barcode"}]},
    }, headers=auth_headers)
    assert resp.status_code == 201


def test_product_history_tracks_price_changes(client, auth_headers):
    product = _create_product(client, auth_headers, sku="HIST-SKU")
    client.patch(f"/api/v1/products/{product['id']}", json={"price": 15.0}, headers=auth_headers)

    resp = client.get(f"/api/v1/products/{product['id']}/history", headers=auth_headers)
    assert resp.status_code == 200
    history = resp.get_json()["data"]
    assert any(h["change_type"] == "price" for h in history)


def test_product_archive_and_restore(client, auth_headers):
    product = _create_product(client, auth_headers, sku="ARCHIVE-SKU")
    client.delete(f"/api/v1/products/{product['id']}", headers=auth_headers)

    resp = client.get(f"/api/v1/products/{product['id']}", headers=auth_headers)
    assert resp.get_json()["data"]["is_active"] is False

    resp = client.post(f"/api/v1/products/{product['id']}/restore", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.get_json()["data"]["is_active"] is True


def test_receipt_verification_public(client, auth_headers):
    product = _create_product(client, auth_headers, sku="VERIFY-SKU", stock=5)
    sale_resp = client.post("/api/v1/sales", json={
        "items": [{"product_id": product["id"], "quantity": 1}],
        "payments": [{"method": "cash", "amount": 10.0, "amount_tendered": 10.0}],
    }, headers=auth_headers)
    sale = sale_resp.get_json()["data"]

    # Fetch the verification code directly since it's not in the sale response by default.
    detail_resp = client.get(f"/api/v1/sales/{sale['id']}", headers=auth_headers)
    verification_code = detail_resp.get_json()["data"].get("verification_code")
    assert verification_code

    # No auth header — this must be public.
    resp = client.get(f"/api/v1/sales/verify/{verification_code}")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["valid"] is True
    assert data["status"] == "completed"


def test_sale_timeline(client, auth_headers):
    product = _create_product(client, auth_headers, sku="TIMELINE-SKU", stock=5)
    sale_resp = client.post("/api/v1/sales", json={
        "items": [{"product_id": product["id"], "quantity": 1}],
        "payments": [{"method": "cash", "amount": 10.0, "amount_tendered": 10.0}],
    }, headers=auth_headers)
    sale_id = sale_resp.get_json()["data"]["id"]

    resp = client.get(f"/api/v1/sales/{sale_id}/timeline", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.get_json()["data"]) >= 1


def test_daily_closing_report(client, auth_headers):
    _create_product(client, auth_headers, sku="CLOSING-SKU")
    resp = client.get("/api/v1/reports/daily-closing", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    for key in ("sales", "profit", "payments_by_method", "cashier_performance", "inventory_summary", "hardware_status"):
        assert key in data

    pdf_resp = client.get("/api/v1/reports/daily-closing/pdf", headers=auth_headers)
    assert pdf_resp.status_code == 200
    assert pdf_resp.content_type == "application/pdf"


def test_product_analytics(client, auth_headers):
    resp = client.get("/api/v1/reports/product-analytics", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    for key in ("top_selling", "highest_revenue", "highest_profit", "fastest_growing", "slow_moving", "most_refunded"):
        assert key in data


def test_business_calendar(client, auth_headers):
    resp = client.get("/api/v1/reports/calendar?year=2026&month=7", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert len(data["days"]) == 31


def test_draft_sales_recovery(client, auth_headers):
    resp = client.post("/api/v1/checkout/start", json={}, headers=auth_headers)
    assert resp.status_code == 201

    resp = client.get("/api/v1/checkout/drafts", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.get_json()["data"]) >= 1


def test_notification_archive(client, auth_headers):
    resp = client.post("/api/v1/notifications", json={
        "type": "system", "title": "Test notification",
    }, headers=auth_headers)
    notif_id = resp.get_json()["data"]["id"]

    resp = client.post(f"/api/v1/notifications/{notif_id}/archive", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.get_json()["data"]["is_archived"] is True

    resp = client.get("/api/v1/notifications", headers=auth_headers)
    ids = [n["id"] for n in resp.get_json()["data"]]
    assert notif_id not in ids


def test_printer_history(client, auth_headers):
    resp = client.post("/api/v1/printers", json={
        "name": "History Printer", "connection_type": "usb", "identifier": "hist-usb-1",
    }, headers=auth_headers)
    printer_id = resp.get_json()["data"]["id"]

    client.post(f"/api/v1/printers/{printer_id}/test-print", headers=auth_headers)

    resp = client.get(f"/api/v1/printers/{printer_id}/history", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.get_json()["data"]) == 1
    assert resp.get_json()["data"][0]["job_type"] == "test"

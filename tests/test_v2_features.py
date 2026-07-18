def test_register_and_default_printer(client, auth_headers):
    resp = client.post("/api/v1/printers", json={
        "name": "Front Counter Printer", "connection_type": "network",
        "identifier": "192.168.1.50:9100", "ip_address": "192.168.1.50",
    }, headers=auth_headers)
    assert resp.status_code == 201
    printer_id = resp.get_json()["data"]["id"]

    resp = client.post(f"/api/v1/printers/{printer_id}/set-default", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.get_json()["data"]["is_default"] is True

    resp = client.post(f"/api/v1/printers/{printer_id}/test-print", headers=auth_headers)
    assert resp.status_code == 200


def test_printer_discover_upserts(client, auth_headers):
    resp = client.post("/api/v1/printers/discover", json={
        "discovered": [{"name": "USB Printer", "connection_type": "usb", "identifier": "usb-001"}]
    }, headers=auth_headers)
    assert resp.status_code == 200
    identifiers = [p["identifier"] for p in resp.get_json()["data"]]
    assert "usb-001" in identifiers


def _create_product(client, auth_headers, sku="VAR-SKU", stock=10):
    resp = client.post("/api/v1/products", json={
        "sku": sku, "name": "Coca-Cola", "price": 1.0, "cost_price": 0.4,
        "tax_rate": 0, "initial_stock": stock, "low_stock_threshold": 2,
    }, headers=auth_headers)
    return resp.get_json()["data"]


def test_product_variants(client, auth_headers):
    product = _create_product(client, auth_headers, sku="COLA-V")
    resp = client.post(f"/api/v1/products/{product['id']}/variants", json={
        "name": "500ml", "sku": "COLA-500", "price": 1.5, "cost_price": 0.6, "stock_quantity": 20,
    }, headers=auth_headers)
    assert resp.status_code == 201
    variant = resp.get_json()["data"]
    assert variant["stock_quantity"] == 20

    resp = client.post(f"/api/v1/products/{product['id']}/variants/{variant['id']}/stock",
                        json={"quantity_change": -5, "reason": "test sale"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.get_json()["data"]["stock_quantity"] == 15


def test_product_units(client, auth_headers):
    product = _create_product(client, auth_headers, sku="SUGAR-U")
    resp = client.post(f"/api/v1/products/{product['id']}/units", json={
        "unit_name": "kg", "conversion_ratio": 1000, "price": 2.5,
    }, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.get_json()["data"]["conversion_ratio"] == 1000.0


def test_checkout_session_cash_flow(client, auth_headers):
    product = _create_product(client, auth_headers, sku="CHECKOUT-1", stock=10)

    resp = client.post("/api/v1/checkout/start", json={}, headers=auth_headers)
    assert resp.status_code == 201
    sale_id = resp.get_json()["data"]["id"]
    assert resp.get_json()["data"]["status"] == "draft"

    resp = client.put(f"/api/v1/checkout/{sale_id}/items", json={
        "items": [{"product_id": product["id"], "quantity": 3}],
    }, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.get_json()["data"]["total_amount"] == 3.0

    # Customer selects cash on the (unauthenticated) display endpoint.
    resp = client.post(f"/api/v1/checkout/{sale_id}/customer-payment-method",
                        json={"method": "cash"})
    assert resp.status_code == 200

    resp = client.post(f"/api/v1/checkout/{sale_id}/confirm-cash",
                        json={"amount_tendered": 5.0}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.get_json()["data"]["status"] == "completed"

    # Stock should now be deducted.
    inv_resp = client.get(f"/api/v1/inventory/product/{product['id']}", headers=auth_headers)
    assert inv_resp.get_json()["data"]["quantity"] == 7


def test_checkout_session_chapa_placeholder_flow(client, auth_headers):
    product = _create_product(client, auth_headers, sku="CHECKOUT-CHAPA", stock=5)
    resp = client.post("/api/v1/checkout/start", json={}, headers=auth_headers)
    sale_id = resp.get_json()["data"]["id"]

    client.put(f"/api/v1/checkout/{sale_id}/items", json={
        "items": [{"product_id": product["id"], "quantity": 1}],
    }, headers=auth_headers)

    resp = client.post(f"/api/v1/checkout/{sale_id}/customer-payment-method",
                        json={"method": "chapa"})
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert "checkout_url" in data
    assert "qr_code_base64" in data


def test_active_sessions_listed_after_login(client, auth_headers):
    resp = client.get("/api/v1/sessions/me", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.get_json()["data"]) >= 1


def test_dashboard_summary_v2_sections(client, auth_headers):
    resp = client.get("/api/v1/dashboard/summary", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    for key in ("sales", "inventory", "payments", "staff", "hardware", "recent_activity", "insights"):
        assert key in data


def test_bulk_barcode_generation_and_labels(client, auth_headers):
    product = _create_product(client, auth_headers, sku="OIL-5L")
    resp = client.post(f"/api/v1/products/{product['id']}/barcodes/bulk-generate",
                        json={"quantity": 5, "batch_label": "test batch"}, headers=auth_headers)
    assert resp.status_code == 201
    entries = resp.get_json()["data"]
    assert len(entries) == 5

    ids = [e["id"] for e in entries]
    resp = client.post(f"/api/v1/products/{product['id']}/barcodes/print-labels",
                        json={"barcode_ids": ids, "label_size": "small"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.content_type == "application/pdf"
    assert len(resp.data) > 100


def test_full_backup_zip_and_verify(client, auth_headers):
    resp = client.post("/api/v1/backup/full", headers=auth_headers)
    assert resp.status_code == 201
    backup = resp.get_json()["data"]
    assert backup["status"] == "completed"

    resp = client.get(f"/api/v1/backup/{backup['id']}/download", headers=auth_headers)
    assert resp.status_code == 200
    zip_bytes = resp.data

    import io
    resp = client.post("/api/v1/backup/verify", data={
        "file": (io.BytesIO(zip_bytes), "backup.zip")
    }, headers=auth_headers, content_type="multipart/form-data")
    assert resp.status_code == 200
    assert resp.get_json()["data"]["app"] == "NovaPOS"


def test_refund_search_and_approval_workflow(client, auth_headers):
    product = _create_product(client, auth_headers, sku="REFUND-SKU", stock=10)
    sale_resp = client.post("/api/v1/sales", json={
        "items": [{"product_id": product["id"], "quantity": 4}],
        "payments": [{"method": "cash", "amount": 4.0, "amount_tendered": 4.0}],
    }, headers=auth_headers)
    sale = sale_resp.get_json()["data"]

    resp = client.get(f"/api/v1/refunds/search?receipt_number={sale['receipt_number']}",
                       headers=auth_headers)
    assert resp.status_code == 200
    results = resp.get_json()["data"]
    assert results[0]["purchase_age"] is not None
    assert results[0]["refund_eligible"] is True

    item_id = sale["items"][0]["id"]
    resp = client.post(f"/api/v1/refunds/sale/{sale['id']}/request", json={
        "sale_item_id": item_id, "quantity": 1, "reason": "damaged",
    }, headers=auth_headers)
    assert resp.status_code == 201
    refund = resp.get_json()["data"]
    assert refund["status"] == "pending"

    resp = client.post(f"/api/v1/refunds/{refund['id']}/approve", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.get_json()["data"]["status"] == "completed"


def test_branding_and_tax_config(client, auth_headers):
    resp = client.get("/api/v1/branding")
    assert resp.status_code == 200

    resp = client.patch("/api/v1/branding", json={"business_name": "Test Store"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.get_json()["data"]["business_name"] == "Test Store"

    resp = client.patch("/api/v1/branding/tax", json={"tax_name": "GST", "default_tax_rate": 15},
                         headers=auth_headers)
    assert resp.status_code == 200
    assert resp.get_json()["data"]["tax_name"] == "GST"


def test_system_health(client, auth_headers):
    resp = client.get("/api/v1/system/health", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["database"]["status"] == "ok"
    assert "resources" in data


def test_direct_checkout_supports_variant_and_discount(client, auth_headers):
    """The one-shot /sales checkout should resolve variants/units/discounts
    the same way the customer-display checkout session does."""
    product = _create_product(client, auth_headers, sku="DIRECT-VARIANT", stock=10)

    variant_resp = client.post(f"/api/v1/products/{product['id']}/variants", json={
        "name": "1L", "sku": "DIRECT-VARIANT-1L", "price": 3.0, "cost_price": 1.2, "stock_quantity": 15,
    }, headers=auth_headers)
    variant = variant_resp.get_json()["data"]

    resp = client.post("/api/v1/sales", json={
        "items": [{
            "product_id": product["id"], "variant_id": variant["id"], "quantity": 2,
            "discount_type": "fixed", "discount_value": 1.0, "discount_reason": "loyal customer",
        }],
        "payments": [{"method": "cash", "amount": 5.0, "amount_tendered": 5.0}],
    }, headers=auth_headers)

    assert resp.status_code == 201
    sale = resp.get_json()["data"]
    # 2 x 3.0 = 6.0, minus 1.0 discount = 5.0 total (no tax configured on this product).
    assert sale["total_amount"] == 5.0

    variant_check = client.get(f"/api/v1/products/{product['id']}/variants/{variant['id']}",
                                headers=auth_headers)
    assert variant_check.get_json()["data"]["stock_quantity"] == 13


def test_product_export_csv(client, auth_headers):
    _create_product(client, auth_headers, sku="EXPORT-SKU")
    resp = client.get("/api/v1/products/bulk/export.csv", headers=auth_headers)
    assert resp.status_code == 200
    assert b"EXPORT-SKU" in resp.data

# NovaPOS API Reference

Base URL (local dev): `http://localhost:5000`
All endpoints are versioned under `/api/v1`. Interactive Swagger UI is always
available at **`/docs`** (and the raw spec at `/openapi.json`) — use this
reference for copy-paste `curl` examples, use `/docs` to explore live.

## Conventions

- **Auth header:** `Authorization: Bearer <access_token>` on every endpoint marked 🔒.
- **Response envelope:** every JSON response looks like:
  ```json
  { "success": true, "message": "...", "data": { ... }, "meta": { ... } }
  ```
  `meta` only appears on paginated list endpoints (`page`, `per_page`, `total_items`, `total_pages`, `has_next`, `has_prev`).
- **Pagination params** (list endpoints): `?page=1&per_page=20`
- **Errors:** `{ "success": false, "message": "...", "errors": {...}, "error_code": "..." }` with an appropriate HTTP status (400/401/403/404/409/422/429/500).
- Endpoints marked **(no auth)** are intentionally public — they're called by unauthenticated hardware (printers, customer displays) or public pages (login screen branding).

Throughout, `$TOKEN` = an access token obtained from `/api/v1/auth/login`.

---

## Auth (`/api/v1/auth`)

**POST `/login`** (no auth, rate-limited 60/min)
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```
Optional headers: `X-Terminal-Id: <device_id>` to associate the session with a POS terminal.
Returns `{ access_token, refresh_token, user }`.

**POST `/refresh`** 🔒 (requires the *refresh* token, not the access token)
```bash
curl -X POST http://localhost:5000/api/v1/auth/refresh \
  -H "Authorization: Bearer $REFRESH_TOKEN"
```

**POST `/register`** — create a user (typically admin-only in practice via `/users` instead)
```bash
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"jdoe","full_name":"Jane Doe","password":"secret123","role_name":"cashier"}'
```

**POST `/change-password`** 🔒
```bash
curl -X POST http://localhost:5000/api/v1/auth/change-password \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"current_password":"admin123","new_password":"newSecret123"}'
```

**GET `/me`** 🔒 — current user profile
```bash
curl http://localhost:5000/api/v1/auth/me -H "Authorization: Bearer $TOKEN"
```

---

## Users (`/api/v1/users`) 🔒 requires `users.view` / `users.manage`

**GET `""`** — list users (paginated)
```bash
curl "http://localhost:5000/api/v1/users?page=1&per_page=20" -H "Authorization: Bearer $TOKEN"
```

**POST `""`** — create a user
```bash
curl -X POST http://localhost:5000/api/v1/users -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"username":"cashier1","full_name":"Sam Cashier","password":"secret123","role_name":"cashier"}'
```

**GET `/<user_id>`** / **PATCH `/<user_id>`** / **DELETE `/<user_id>`** (deactivate)
```bash
curl http://localhost:5000/api/v1/users/2 -H "Authorization: Bearer $TOKEN"
curl -X PATCH http://localhost:5000/api/v1/users/2 -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"full_name":"Samuel Cashier"}'
curl -X DELETE http://localhost:5000/api/v1/users/2 -H "Authorization: Bearer $TOKEN"
```

**POST `/<user_id>/reactivate`**
```bash
curl -X POST http://localhost:5000/api/v1/users/2/reactivate -H "Authorization: Bearer $TOKEN"
```

**POST `/<user_id>/reset-password`**
```bash
curl -X POST http://localhost:5000/api/v1/users/2/reset-password -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"new_password":"newSecret123"}'
```

---

## Roles (`/api/v1/roles`) 🔒 `users.manage` for writes

```bash
curl http://localhost:5000/api/v1/roles -H "Authorization: Bearer $TOKEN"

curl -X POST http://localhost:5000/api/v1/roles -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"supervisor","description":"Shift supervisor","permissions":["sales.manage","refunds.manage","reports.view"]}'

curl http://localhost:5000/api/v1/roles/1 -H "Authorization: Bearer $TOKEN"

curl -X PATCH http://localhost:5000/api/v1/roles/1 -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"permissions":["sales.manage","refunds.manage"]}'

curl -X DELETE http://localhost:5000/api/v1/roles/1 -H "Authorization: Bearer $TOKEN"
```

---

## Categories (`/api/v1/categories`) 🔒 read for any logged-in user, `categories.manage` for writes

```bash
curl "http://localhost:5000/api/v1/categories?active_only=true" -H "Authorization: Bearer $TOKEN"

curl -X POST http://localhost:5000/api/v1/categories -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Beverages","description":"Drinks and juices"}'

curl http://localhost:5000/api/v1/categories/1 -H "Authorization: Bearer $TOKEN"
curl -X PATCH http://localhost:5000/api/v1/categories/1 -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"description":"Updated description"}'
curl -X DELETE http://localhost:5000/api/v1/categories/1 -H "Authorization: Bearer $TOKEN"
```

---

## Products (`/api/v1/products`) 🔒 read for any logged-in user, `products.manage` for writes

**GET `""`** — list, with search/sort/pagination/filters
```bash
curl "http://localhost:5000/api/v1/products?search=cola&category_id=1&active_only=true&sort_by=name&sort_dir=asc&page=1&per_page=20" \
  -H "Authorization: Bearer $TOKEN"
```

**POST `""`** — create
```bash
curl -X POST http://localhost:5000/api/v1/products -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "sku": "COLA-001", "name": "Cola 330ml", "price": 1.50, "cost_price": 0.60,
    "tax_rate": 15, "category_id": 1, "unit": "pcs",
    "initial_stock": 100, "low_stock_threshold": 10,
    "generate_barcode": true, "is_tax_exempt": false
  }'
```

**GET / PATCH / DELETE `/<product_id>`**
```bash
curl http://localhost:5000/api/v1/products/1 -H "Authorization: Bearer $TOKEN"
curl -X PATCH http://localhost:5000/api/v1/products/1 -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"price": 1.75}'
curl -X DELETE http://localhost:5000/api/v1/products/1 -H "Authorization: Bearer $TOKEN"
```

**GET `/barcode/<barcode>`** — lookup by barcode (used by scanner-equipped cashier UI)
```bash
curl http://localhost:5000/api/v1/products/barcode/648593421305 -H "Authorization: Bearer $TOKEN"
```

**POST `/<product_id>/barcode`** — assign/generate a single barcode
```bash
curl -X POST http://localhost:5000/api/v1/products/1/barcode -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{}'
# or with an explicit code: -d '{"code":"1234567890123"}'
```

**POST `/<product_id>/image`** — upload product image (multipart)
```bash
curl -X POST http://localhost:5000/api/v1/products/1/image -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/photo.jpg"
```

### Bulk import/export (`/api/v1/products/bulk`)
```bash
curl "http://localhost:5000/api/v1/products/bulk/export.csv"  -H "Authorization: Bearer $TOKEN" -o products.csv
curl "http://localhost:5000/api/v1/products/bulk/export.xlsx" -H "Authorization: Bearer $TOKEN" -o products.xlsx
curl "http://localhost:5000/api/v1/products/bulk/export.json" -H "Authorization: Bearer $TOKEN" -o products.json

curl -X POST http://localhost:5000/api/v1/products/bulk/import -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/products.csv"
```
CSV/XLSX columns: `sku, barcode, name, description, price, cost_price, tax_rate, category_name, unit, current_stock, is_active`. Existing SKUs are updated; new SKUs are created (with `current_stock` as initial stock).

### Product variants (`/api/v1/products/<product_id>/variants`)
```bash
curl http://localhost:5000/api/v1/products/1/variants -H "Authorization: Bearer $TOKEN"

curl -X POST http://localhost:5000/api/v1/products/1/variants -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"500ml","sku":"COLA-500","price":1.90,"cost_price":0.80,"stock_quantity":50,"low_stock_threshold":5}'

curl http://localhost:5000/api/v1/products/1/variants/3 -H "Authorization: Bearer $TOKEN"
curl -X PATCH http://localhost:5000/api/v1/products/1/variants/3 -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"price": 2.00}'
curl -X DELETE http://localhost:5000/api/v1/products/1/variants/3 -H "Authorization: Bearer $TOKEN"

curl -X POST http://localhost:5000/api/v1/products/1/variants/3/stock -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"quantity_change": 20, "reason": "New shipment"}'
```

### Alternate units (`/api/v1/products/<product_id>/units`)
```bash
curl http://localhost:5000/api/v1/products/1/units -H "Authorization: Bearer $TOKEN"

curl -X POST http://localhost:5000/api/v1/products/1/units -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"unit_name":"kg","conversion_ratio":1000,"price":2.50}'
# conversion_ratio is in terms of the product's base inventory unit (e.g. grams).

curl -X PATCH http://localhost:5000/api/v1/products/1/units/2 -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"price": 2.75}'
curl -X DELETE http://localhost:5000/api/v1/products/1/units/2 -H "Authorization: Bearer $TOKEN"
```

### Advanced barcode management (`/api/v1/products/<product_id>/barcodes`)
```bash
# Register a scanned manufacturer barcode (duplicate-safe; re-scans are no-ops)
curl -X POST http://localhost:5000/api/v1/products/1/barcodes/scan -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"code":"6291041500213"}'

# Bulk-generate 100 unique internal barcodes for a new stock batch
curl -X POST http://localhost:5000/api/v1/products/1/barcodes/bulk-generate -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"quantity": 100, "batch_label": "July 2026 batch"}'

# List previously generated barcodes for this product
curl http://localhost:5000/api/v1/products/1/barcodes -H "Authorization: Bearer $TOKEN"

# Print a PDF sheet of Code128 labels for specific generated barcodes
curl -X POST http://localhost:5000/api/v1/products/1/barcodes/print-labels -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"barcode_ids": [1,2,3,4,5], "label_size": "medium", "show_price": true, "show_sku": true}' \
  -o labels.pdf
```

---

## Inventory (`/api/v1/inventory`) 🔒 `inventory.view` / `inventory.manage`

```bash
curl "http://localhost:5000/api/v1/inventory?page=1&per_page=20" -H "Authorization: Bearer $TOKEN"
curl http://localhost:5000/api/v1/inventory/low-stock -H "Authorization: Bearer $TOKEN"
curl http://localhost:5000/api/v1/inventory/product/1 -H "Authorization: Bearer $TOKEN"

curl -X POST http://localhost:5000/api/v1/inventory/product/1/restock -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"quantity": 50, "reason": "Weekly delivery"}'

curl -X POST http://localhost:5000/api/v1/inventory/product/1/adjust -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"quantity_change": -3, "reason": "Damaged in storage"}'

curl -X PATCH http://localhost:5000/api/v1/inventory/product/1/thresholds -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"low_stock_threshold": 15, "reorder_quantity": 40}'

curl http://localhost:5000/api/v1/inventory/product/1/history -H "Authorization: Bearer $TOKEN"

curl http://localhost:5000/api/v1/inventory/export.csv -H "Authorization: Bearer $TOKEN" -o inventory.csv
```

---

## Sales / Checkout (`/api/v1/sales`) 🔒 `sales.create` to check out, `sales.view`/`sales.manage` to read/void

**POST `""`** — direct one-shot checkout (no customer display involved)
```bash
curl -X POST http://localhost:5000/api/v1/sales -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"product_id": 1, "quantity": 2},
      {"product_id": 2, "variant_id": 5, "quantity": 1, "discount_type": "fixed", "discount_value": 0.50, "discount_reason": "Loyal customer"}
    ],
    "payments": [{"method": "cash", "amount": 10.00, "amount_tendered": 10.00}],
    "customer_id": 3,
    "discount_amount": 0.5,
    "discount_reason": "Promotional offer"
  }'
```
An item may specify `product_id` alone, or add `variant_id` (specific variant) and/or `unit_id` (alternate selling unit — `quantity` is then in that unit, converted to base stock automatically).

**GET `""`** — list sales (paginated) · **GET `/search`** — receipt history search
```bash
curl "http://localhost:5000/api/v1/sales?page=1&per_page=20" -H "Authorization: Bearer $TOKEN"

curl "http://localhost:5000/api/v1/sales/search?receipt_number=NP-20260709&customer_id=3&cashier_id=2&payment_method=cash&start_date=2026-07-01&end_date=2026-07-09" \
  -H "Authorization: Bearer $TOKEN"
```

**GET `/<sale_id>`** · **GET `/receipt/<receipt_number>`**
```bash
curl http://localhost:5000/api/v1/sales/10 -H "Authorization: Bearer $TOKEN"
curl http://localhost:5000/api/v1/sales/receipt/NP-20260709-8F3K1Q -H "Authorization: Bearer $TOKEN"
```

**GET `/<sale_id>/receipt-text`** (plain text, for thermal printers) · **GET `/<sale_id>/receipt-pdf`** (download)
```bash
curl http://localhost:5000/api/v1/sales/10/receipt-text -H "Authorization: Bearer $TOKEN"
curl http://localhost:5000/api/v1/sales/10/receipt-pdf -H "Authorization: Bearer $TOKEN" -o receipt.pdf
```

**POST `/<sale_id>/void`**
```bash
curl -X POST http://localhost:5000/api/v1/sales/10/void -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"reason": "Customer changed their mind"}'
```

**POST `/<sale_id>/print`** — (re)send the receipt to a printer (retry / choose another printer)
```bash
curl -X POST http://localhost:5000/api/v1/sales/10/print -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"printer_id": 2}'
```

---

## Checkout Sessions — customer display flow (`/api/v1/checkout`)

Used when a customer display is connected: the cashier opens a session, cart updates stream live to the display, and the customer picks their own payment method.

**POST `/start`** 🔒
```bash
curl -X POST http://localhost:5000/api/v1/checkout/start -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"terminal_id": 1, "customer_id": null}'
```

**PUT `/<sale_id>/items`** 🔒 — replace the cart (send the full cart every time it changes)
```bash
curl -X PUT http://localhost:5000/api/v1/checkout/12/items -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "items": [{"product_id": 1, "quantity": 3}],
    "cart_discount_amount": 1.0,
    "cart_discount_reason": "Manager approved"
  }'
```

**POST `/<sale_id>/customer-payment-method`** (no auth — called directly by the customer display)
```bash
curl -X POST http://localhost:5000/api/v1/checkout/12/customer-payment-method \
  -H "Content-Type: application/json" -d '{"method": "cash"}'
# or: {"method": "chapa", "customer_email": "buyer@example.com", "customer_name": "Jane Buyer"}
# or: {"method": "offline"}
```
For `chapa`, the response includes `checkout_url` and `qr_code_base64` (a PNG the customer display can render for the customer to scan).

**POST `/<sale_id>/confirm-cash`** 🔒 — cashier confirms cash received
```bash
curl -X POST http://localhost:5000/api/v1/checkout/12/confirm-cash -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"amount_tendered": 20.00}'
```

**POST `/<sale_id>/reject-cash`** 🔒 — cashier rejects (e.g. counterfeit), lets customer choose again
```bash
curl -X POST http://localhost:5000/api/v1/checkout/12/reject-cash -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"reason": "Torn note"}'
```

**POST `/<sale_id>/confirm-offline`** 🔒 — cashier confirms an offline payment (card machine, bank transfer, voucher)
```bash
curl -X POST http://localhost:5000/api/v1/checkout/12/confirm-offline -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"reference": "Card machine ref #4471"}'
```

**POST `/<sale_id>/cancel`** 🔒
```bash
curl -X POST http://localhost:5000/api/v1/checkout/12/cancel -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"reason": "Customer left"}'
```

---

## Payments (`/api/v1/payments`)

**GET `/sale/<sale_id>`** 🔒
```bash
curl http://localhost:5000/api/v1/payments/sale/10 -H "Authorization: Bearer $TOKEN"
```

**POST `/chapa/webhook`** (no auth — called by Chapa's servers, not your frontend)
Configure this URL (`https://yourdomain.com/api/v1/payments/chapa/webhook`) in your Chapa dashboard. Verifies the `Chapa-Signature` header against `CHAPA_WEBHOOK_SECRET`, re-verifies the transaction directly with Chapa, then finalizes the sale.

---

## Refunds (`/api/v1/refunds`) 🔒 `refunds.create` / `refunds.manage`

**GET `/search`** — find a sale to refund by receipt number/barcode or a scanned product barcode
```bash
curl "http://localhost:5000/api/v1/refunds/search?receipt_number=NP-20260709-8F3K1Q" -H "Authorization: Bearer $TOKEN"
curl "http://localhost:5000/api/v1/refunds/search?product_barcode=648593421305" -H "Authorization: Bearer $TOKEN"
```
Each result includes `purchase_age` (e.g. `"2 hours ago"`), `refund_eligible`, and each item's `refundable_quantity`.

**POST `/sale/<sale_id>`** — direct refund (completes immediately)
```bash
curl -X POST http://localhost:5000/api/v1/refunds/sale/10 -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"sale_item_id": 22, "quantity": 1, "reason": "Damaged packaging"}'
```

**POST `/sale/<sale_id>/request`** — request a refund pending manager approval
```bash
curl -X POST http://localhost:5000/api/v1/refunds/sale/10/request -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"sale_item_id": 22, "quantity": 1, "reason": "Customer says it arrived broken"}'
```

**POST `/<refund_id>/approve`** / **POST `/<refund_id>/reject`**
```bash
curl -X POST http://localhost:5000/api/v1/refunds/5/approve -H "Authorization: Bearer $TOKEN"
curl -X POST http://localhost:5000/api/v1/refunds/5/reject -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"reason": "Outside the 30-day window"}'
```

**GET `/sale/<sale_id>/list`** · **GET `/history`**
```bash
curl http://localhost:5000/api/v1/refunds/sale/10/list -H "Authorization: Bearer $TOKEN"
curl "http://localhost:5000/api/v1/refunds/history?page=1&per_page=20" -H "Authorization: Bearer $TOKEN"
```

---

## Customers (`/api/v1/customers`) 🔒 read for logged-in users, `customers.manage` for writes

```bash
curl "http://localhost:5000/api/v1/customers?active_only=true" -H "Authorization: Bearer $TOKEN"

curl -X POST http://localhost:5000/api/v1/customers -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Jane Buyer","email":"jane@example.com","phone":"+251911223344"}'

curl http://localhost:5000/api/v1/customers/3 -H "Authorization: Bearer $TOKEN"
curl -X PATCH http://localhost:5000/api/v1/customers/3 -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"phone":"+251911999999"}'
curl -X DELETE http://localhost:5000/api/v1/customers/3 -H "Authorization: Bearer $TOKEN"

curl http://localhost:5000/api/v1/customers/3/purchase-history -H "Authorization: Bearer $TOKEN"
curl http://localhost:5000/api/v1/customers/export.csv -H "Authorization: Bearer $TOKEN" -o customers.csv
```

---

## Reports (`/api/v1/reports`) 🔒 `reports.view`

`period` is one of `today | week | month | year | custom` (for `custom`, also pass `start_date`/`end_date` as ISO datetimes).
```bash
curl "http://localhost:5000/api/v1/reports/sales?period=today" -H "Authorization: Bearer $TOKEN"
curl "http://localhost:5000/api/v1/reports/profit?period=month" -H "Authorization: Bearer $TOKEN"
curl "http://localhost:5000/api/v1/reports/top-products?period=week&limit=5" -H "Authorization: Bearer $TOKEN"
curl "http://localhost:5000/api/v1/reports/inventory" -H "Authorization: Bearer $TOKEN"
```

---

## Dashboard (`/api/v1/dashboard`) 🔒 `dashboard.view`

```bash
curl http://localhost:5000/api/v1/dashboard/summary -H "Authorization: Bearer $TOKEN"
```
Returns `sales`, `inventory`, `payments`, `staff`, `hardware`, `recent_activity`, and plain-language `insights` (e.g. *"Sales increased by 15% compared to yesterday."*).

---

## Notifications (`/api/v1/notifications`) 🔒

```bash
curl "http://localhost:5000/api/v1/notifications?unread_only=true" -H "Authorization: Bearer $TOKEN"

curl -X POST http://localhost:5000/api/v1/notifications -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"type":"system","title":"Maintenance tonight","message":"Server restarts at 2am.","severity":"info"}'

curl -X POST http://localhost:5000/api/v1/notifications/7/read -H "Authorization: Bearer $TOKEN"
```

---

## Printers (`/api/v1/printers`) — see the "Hardware" section of the README for the full connect/test walkthrough

```bash
curl http://localhost:5000/api/v1/printers -H "Authorization: Bearer $TOKEN"

curl -X POST http://localhost:5000/api/v1/printers -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Front Counter","connection_type":"network","identifier":"192.168.1.50:9100","ip_address":"192.168.1.50","profile_type":"receipt"}'

curl -X POST http://localhost:5000/api/v1/printers/discover -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"discovered":[{"name":"USB Printer","connection_type":"usb","identifier":"usb-0001","manufacturer":"Epson","model":"TM-T20"}]}'

curl http://localhost:5000/api/v1/printers/1 -H "Authorization: Bearer $TOKEN"
curl -X PATCH http://localhost:5000/api/v1/printers/1 -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Register 1 Printer"}'
curl -X DELETE http://localhost:5000/api/v1/printers/1 -H "Authorization: Bearer $TOKEN"

curl -X POST http://localhost:5000/api/v1/printers/1/set-default -H "Authorization: Bearer $TOKEN"
curl -X POST http://localhost:5000/api/v1/printers/1/test-print -H "Authorization: Bearer $TOKEN"

# Called by the printer/agent itself, no user auth:
curl -X POST http://localhost:5000/api/v1/printers/heartbeat/usb-0001 -H "Content-Type: application/json" -d '{"paper_status":"ok"}'
```

---

## Customer Display Pairing (`/api/v1/pairing`)

```bash
curl http://localhost:5000/api/v1/pairing/discover-terminals   # no auth — automatic discovery

curl -X POST http://localhost:5000/api/v1/pairing/generate-code -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"terminal_id": 1, "server_address": "http://192.168.1.10:5000"}'
# returns { code, expires_at, terminal_id, terminal_name, qr_code_base64 }

curl -X POST http://localhost:5000/api/v1/pairing/redeem -H "Content-Type: application/json" \
  -d '{"code": "420541", "display_identifier": "tablet-abc123", "display_name": "Front Window Display"}'
# no auth — called by the customer display itself
```

---

## Hardware Devices (`/api/v1/hardware`)

```bash
curl http://localhost:5000/api/v1/hardware/devices -H "Authorization: Bearer $TOKEN"

curl -X POST http://localhost:5000/api/v1/hardware/devices -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Register 1","device_type":"pos_terminal","identifier":"term-001"}'
# device_type: pos_terminal | customer_display | receipt_printer | barcode_scanner | cash_drawer

curl http://localhost:5000/api/v1/hardware/devices/1 -H "Authorization: Bearer $TOKEN"
curl -X PATCH http://localhost:5000/api/v1/hardware/devices/1 -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"ip_address":"192.168.1.20"}'
curl -X DELETE http://localhost:5000/api/v1/hardware/devices/1 -H "Authorization: Bearer $TOKEN"

curl -X POST http://localhost:5000/api/v1/hardware/devices/heartbeat/term-001   # no auth

curl -X POST http://localhost:5000/api/v1/hardware/devices/1/open-drawer -H "Authorization: Bearer $TOKEN"
```

---

## Backup & Restore (`/api/v1/backup`) 🔒 `settings.manage`

```bash
curl http://localhost:5000/api/v1/backup -H "Authorization: Bearer $TOKEN"
curl -X POST http://localhost:5000/api/v1/backup -H "Authorization: Bearer $TOKEN"          # DB-only backup
curl -X POST http://localhost:5000/api/v1/backup/full -H "Authorization: Bearer $TOKEN"     # complete ZIP backup

curl http://localhost:5000/api/v1/backup/1/download -H "Authorization: Bearer $TOKEN" -o backup.zip

curl -X POST http://localhost:5000/api/v1/backup/1/restore -H "Authorization: Bearer $TOKEN"  # DB-only restore

curl -X POST http://localhost:5000/api/v1/backup/verify -H "Authorization: Bearer $TOKEN" -F "file=@backup.zip"
curl -X POST http://localhost:5000/api/v1/backup/restore-full -H "Authorization: Bearer $TOKEN" -F "file=@backup.zip"
```

---

## Settings (`/api/v1/settings`) 🔒 read for logged-in users, `settings.manage` for writes

Generic key-value store (business_name, currency, receipt_footer, etc. — see Branding/Tax below for the structured equivalents).
```bash
curl http://localhost:5000/api/v1/settings -H "Authorization: Bearer $TOKEN"
curl -X PUT http://localhost:5000/api/v1/settings -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"key":"currency","value":"ETB"}'
curl http://localhost:5000/api/v1/settings/currency -H "Authorization: Bearer $TOKEN"
```

---

## Branding & Tax (`/api/v1/branding`)

**GET `""`** (no auth — used by login page & customer display) · **PATCH `""`** 🔒
```bash
curl http://localhost:5000/api/v1/branding
curl -X PATCH http://localhost:5000/api/v1/branding -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"business_name":"Nova Mart","address":"Bole Road, Addis Ababa","phone":"+251911000000","email":"info@novamart.com"}'
```

**POST `/logo`** 🔒 (multipart)
```bash
curl -X POST http://localhost:5000/api/v1/branding/logo -H "Authorization: Bearer $TOKEN" -F "file=@logo.png"
```

**GET `/tax`** 🔒 · **PATCH `/tax`** 🔒
```bash
curl http://localhost:5000/api/v1/branding/tax -H "Authorization: Bearer $TOKEN"
curl -X PATCH http://localhost:5000/api/v1/branding/tax -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"tax_enabled": true, "tax_name": "VAT", "default_tax_rate": 15, "prices_include_tax": false}'
```

---

## System Health & Logs (`/api/v1/system`) 🔒

```bash
curl http://localhost:5000/api/v1/system/health -H "Authorization: Bearer $TOKEN"
curl "http://localhost:5000/api/v1/system/logs?category=payments&severity=error" -H "Authorization: Bearer $TOKEN"
```

---

## Sessions (`/api/v1/sessions`) 🔒

```bash
curl http://localhost:5000/api/v1/sessions -H "Authorization: Bearer $TOKEN"          # all active sessions (settings.manage)
curl http://localhost:5000/api/v1/sessions/me -H "Authorization: Bearer $TOKEN"       # my own sessions
curl http://localhost:5000/api/v1/sessions/user/2/history -H "Authorization: Bearer $TOKEN"

curl -X POST http://localhost:5000/api/v1/sessions/9/revoke -H "Authorization: Bearer $TOKEN"
curl -X POST http://localhost:5000/api/v1/sessions/user/2/force-logout -H "Authorization: Bearer $TOKEN"
```

---

## Audit Log (`/api/v1/audit`) 🔒 `settings.manage`

```bash
curl "http://localhost:5000/api/v1/audit?page=1&per_page=20" -H "Authorization: Bearer $TOKEN"
curl http://localhost:5000/api/v1/audit/entity/product/1 -H "Authorization: Bearer $TOKEN"
curl http://localhost:5000/api/v1/audit/user/2 -H "Authorization: Bearer $TOKEN"
```

---

## Gift Cards & Store Credit (`/api/v1/gift-cards`)

```bash
curl -X POST http://localhost:5000/api/v1/gift-cards -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"initial_value": 50.00, "customer_id": 3, "card_type": "gift_card"}'
# card_type: "gift_card" (purchased) or "store_credit" (usually issued automatically from a refund)

curl http://localhost:5000/api/v1/gift-cards/GC-AB12CD34EF/balance -H "Authorization: Bearer $TOKEN"
curl http://localhost:5000/api/v1/gift-cards/GC-AB12CD34EF -H "Authorization: Bearer $TOKEN"
curl http://localhost:5000/api/v1/gift-cards/customer/3 -H "Authorization: Bearer $TOKEN"
curl http://localhost:5000/api/v1/gift-cards/GC-AB12CD34EF/transactions -H "Authorization: Bearer $TOKEN"

curl -X POST http://localhost:5000/api/v1/gift-cards/GC-AB12CD34EF/recharge -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"amount": 20.00}'

# Redeem manually (normally happens automatically as a sale payment method — see below):
curl -X POST http://localhost:5000/api/v1/gift-cards/GC-AB12CD34EF/redeem -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"amount": 10.00}'

curl -X DELETE http://localhost:5000/api/v1/gift-cards/GC-AB12CD34EF -H "Authorization: Bearer $TOKEN"   # deactivate
```

**Using a gift card as a sale payment method:**
```bash
curl -X POST http://localhost:5000/api/v1/sales -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "items": [{"product_id": 1, "quantity": 2}],
    "payments": [{"method": "gift_card", "amount": 20.00, "gift_card_code": "GC-AB12CD34EF"}]
  }'
```

**Store credit from a refund:**
```bash
curl -X POST http://localhost:5000/api/v1/refunds/sale/10 -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"sale_item_id": 22, "quantity": 1, "reason": "Damaged", "as_store_credit": true}'
# requires the sale to have a linked customer_id; issues a new store_credit gift card for them
```

---

## Favorites & Quick-Access (`/api/v1/favorites`)

```bash
curl http://localhost:5000/api/v1/favorites -H "Authorization: Bearer $TOKEN"                 # my pinned products
curl -X POST http://localhost:5000/api/v1/favorites/1 -H "Authorization: Bearer $TOKEN"       # pin product #1
curl -X DELETE http://localhost:5000/api/v1/favorites/1 -H "Authorization: Bearer $TOKEN"     # unpin

curl http://localhost:5000/api/v1/favorites/recently-sold -H "Authorization: Bearer $TOKEN"
curl http://localhost:5000/api/v1/favorites/frequently-sold -H "Authorization: Bearer $TOKEN"
```

---

## Global Search (`/api/v1/search`)

```bash
curl "http://localhost:5000/api/v1/search?q=cola" -H "Authorization: Bearer $TOKEN"
```
Returns up to 8 matches each across `products`, `variants`, `categories`, `customers`, `users`, and `sales` (by receipt number), plus a `total_count`.

---

## Receipt & Label Designer Templates (`/api/v1/templates`)

The frontend owns the actual drag-and-drop editor; this just persists the
resulting layout (an opaque JSON element list — e.g.
`{"elements": [{"type": "logo"}, {"type": "items_table"}, {"type": "qr_code"}]}`)
and tracks the active default.

```bash
curl http://localhost:5000/api/v1/templates/receipts -H "Authorization: Bearer $TOKEN"

curl -X POST http://localhost:5000/api/v1/templates/receipts -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Default 80mm","paper_width_mm":80,"layout":{"elements":[{"type":"logo"},{"type":"items_table"},{"type":"qr_code"}]},"set_default":true}'

curl -X PATCH http://localhost:5000/api/v1/templates/receipts/1 -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"layout": {"elements":[{"type":"store_name"},{"type":"items_table"}]}}'

curl -X POST http://localhost:5000/api/v1/templates/receipts/1/set-default -H "Authorization: Bearer $TOKEN"
curl -X DELETE http://localhost:5000/api/v1/templates/receipts/1 -H "Authorization: Bearer $TOKEN"

# Same shape for labels, under /api/v1/templates/labels (label_size instead of paper_width_mm)
curl -X POST http://localhost:5000/api/v1/templates/labels -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Small Label","label_size":"small","layout":{"elements":[{"type":"barcode"},{"type":"price"}]}}'
```

---

## Product History (`GET /api/v1/products/<id>/history`) & Archive/Restore

```bash
curl http://localhost:5000/api/v1/products/1/history -H "Authorization: Bearer $TOKEN"
# field-level log: price changes, cost_price changes, barcode changes, image updates, archive/restore

curl -X DELETE http://localhost:5000/api/v1/products/1 -H "Authorization: Bearer $TOKEN"    # archive (soft-delete)
curl -X POST http://localhost:5000/api/v1/products/1/restore -H "Authorization: Bearer $TOKEN"  # restore
```

---

## Sale Timeline & Receipt Verification

**GET `/api/v1/sales/<sale_id>/timeline`** 🔒 — full chronological event history for a sale
```bash
curl http://localhost:5000/api/v1/sales/10/timeline -H "Authorization: Bearer $TOKEN"
```

**GET `/api/v1/sales/verify/<verification_code>`** (no auth) — public receipt authenticity check
```bash
curl http://localhost:5000/api/v1/sales/verify/AB3F9K2Q
```
Returns store name, purchase date, items (product/variant/quantity only — no
cashier/customer PII), payment methods, and current status
(`completed`/`voided`/`refunded`/`partially_refunded`). The same code is
encoded in the receipt's QR code (`verify:<code>`).

---

## Advanced Reporting (`/api/v1/reports`)

**GET `/daily-closing`** and **GET `/daily-closing/pdf`** — professional end-of-day report
```bash
curl "http://localhost:5000/api/v1/reports/daily-closing?date=2026-07-09" -H "Authorization: Bearer $TOKEN"
curl "http://localhost:5000/api/v1/reports/daily-closing/pdf?date=2026-07-09" -H "Authorization: Bearer $TOKEN" -o closing_report.pdf
```
Includes sales/profit summary, payment-method breakdown, refunds/discounts totals, per-cashier performance, inventory summary, and hardware status.

**GET `/product-analytics`** — top-selling, highest revenue/profit, fastest-growing, slow-moving, most-refunded, nearing depletion
```bash
curl "http://localhost:5000/api/v1/reports/product-analytics?period=month&limit=10" -H "Authorization: Bearer $TOKEN"
```

**GET `/calendar`** — per-day aggregates for a month (for an interactive business calendar UI)
```bash
curl "http://localhost:5000/api/v1/reports/calendar?year=2026&month=7" -H "Authorization: Bearer $TOKEN"
```

---

## Draft Sales Recovery (`GET /api/v1/checkout/drafts`)

```bash
curl "http://localhost:5000/api/v1/checkout/drafts?mine_only=true" -H "Authorization: Bearer $TOKEN"
```
Every checkout session is persisted as `status="draft"` from the moment
it's created — this just lists them, so a cashier can resume after a
browser crash, power outage, or network drop without losing the cart.

---

## Printer History (`GET /api/v1/printers/<id>/history`)

```bash
curl http://localhost:5000/api/v1/printers/1/history -H "Authorization: Bearer $TOKEN"
```
Every print job (receipt, test, label) is logged with its status
(`sent`/`queued_offline`/`failed`) and a content preview, for troubleshooting
"why didn't this print" questions.

---

## Notification Archive & Filters

```bash
curl "http://localhost:5000/api/v1/notifications?type=low_stock&severity=warning&include_archived=false" \
  -H "Authorization: Bearer $TOKEN"
curl -X POST http://localhost:5000/api/v1/notifications/7/archive -H "Authorization: Bearer $TOKEN"
```

---

## WebSocket events (Socket.IO)

Connect to the same host/port as the REST API (no separate port). After connecting, join a room based on the client's role:

```js
const socket = io("http://localhost:5000");
socket.emit("join", { room: "dashboard" });          // React admin dashboard
socket.emit("join", { room: "pos_terminals" });      // Cashier UI
socket.emit("join", { room: "customer_displays" });  // Customer display
```

| Event | Room | Payload | When |
|---|---|---|---|
| `sale:created` | dashboard, pos_terminals | full sale object | a sale completes |
| `notification:new` | dashboard | `{id, type, title, message, severity}` | any notification is created (low stock, backup done, printer offline, etc.) |
| `checkout:update` | customer_displays | full (draft) sale object | cart items/discounts change during a checkout session |
| `customer:payment_selected` | pos_terminals | `{sale_id, method, checkout_url?}` | customer picks a payment method on the display |
| `payment:confirmed` | customer_displays, pos_terminals | full sale object | cash/offline/Chapa payment is confirmed and the sale completes |
| `print:job` | pos_terminals | `{printer_id, printer_identifier, connection_type, job_type, content}` | a receipt/test print is dispatched — a local agent with driver access performs the actual print |
| `hardware:cash_drawer_open` | pos_terminals | `{device_id}` | cashier opens the cash drawer |
| `activity:new` | dashboard | `{id, action, entity_type, entity_id, user_id, user_name, created_at}` | **every** audited action, live — the "live activity feed" |
| `dashboard:refresh` | dashboard | dashboard summary | (available for future push-refresh use) |

---

## Permission reference

| Role (seeded default) | Key permissions |
|---|---|
| `admin` | `*` (everything) |
| `manager` | products/categories/inventory/sales/customers manage, `reports.view`, `dashboard.view`, `refunds.manage`, `settings.manage`, `users.view` |
| `cashier` | `sales.create`, `sales.view`, `products.view`, `customers.view`/`manage`, `payments.create`, `refunds.create`, `dashboard.view` |
| `inventory_clerk` | `products.view`/`manage`, `inventory.manage`/`view`, `categories.view`, `dashboard.view` |

Manage roles/permissions at runtime via `/api/v1/roles`.

# NovaPOS Backend

An enterprise-grade, API-first Point-of-Sale backend built with Flask. It is
the single "brain" for every client — React admin dashboard, React cashier
UI, Raspberry Pi/tablet customer display, and future mobile/desktop apps all
talk to the same REST + WebSocket API. **No client ever touches the database
directly.**

- 🧪 Interactive Swagger UI: `http://localhost:5000/docs` (once running)

---

## Table of contents

1. [Architecture](#architecture)
2. [Project structure](#project-structure)
3. [Quick start](#quick-start)
4. [Configuration (.env)](#configuration-env)
5. [Running the server](#running-the-server)
6. [Running tests](#running-tests)
7. [Database migrations](#database-migrations)
8. [V1 feature summary](#v1-feature-summary)
9. [V2 feature summary](#v2-feature-summary)
10. [V3 feature summary](#v3-feature-summary)
11. [Security](#security)
12. [Performance notes](#performance-notes)
13. [Connecting & testing hardware](#connecting--testing-hardware)
    - [Receipt printers](#receipt-printers)
    - [Customer display](#customer-display)
    - [Cash drawer](#cash-drawer)
14. [Chapa payment integration](#chapa-payment-integration)
15. [Backup & restore](#backup--restore)
16. [WebSocket integration guide](#websocket-integration-guide)
17. [Roles & permissions](#roles--permissions)
18. [Building a frontend](#building-a-frontend)
19. [Deployment notes](#deployment-notes)
20. [Troubleshooting](#troubleshooting)

---

## Architecture

```
React Admin Dashboard ─┐
React Cashier UI       ─┤
Customer Display        ─┼──▶  Flask REST API (+ Socket.IO WebSocket)
(tablet/RPi/desktop)    ─┤            │
Future Mobile App       ─┘            ▼
                              Business Logic (Services)
                                      │
                                      ▼
                          Repository / Data Access Layer
                                      │
                                      ▼
                              SQLAlchemy Models
                                      │
                                      ▼
                            SQLite (dev) / PostgreSQL (prod)
```

Layers, strictly separated:

- **models/** — table definitions only, no business logic.
- **repositories/** — pure data access (queries), no business rules.
- **services/** — all business logic (stock checks, checkout flow, receipts,
  reports, refunds, printing, payments).
- **api/v1/** — thin controllers: validate input via schemas, call a service,
  return a standard response envelope.
- **schemas/** — marshmallow request/response validation, also powers the
  auto-generated Swagger docs.
- **core/** — cross-cutting helpers: JWT, password hashing, permissions,
  middleware (CORS, error handling, request logging, rate limiting), and
  utilities (pagination, barcodes, QR codes, receipts, file uploads).
- **websocket/** — Socket.IO events for realtime updates (new sale, low
  stock, live checkout, print jobs, payment confirmation).
- **tasks/** — APScheduler background jobs (nightly backup, notification
  cleanup, daily report snapshot).

---

## Project structure

```
backend/
├── run.py                      # Entrypoint (starts Flask + Socket.IO)
├── requirements.txt
├── .env                        # Environment configuration
├── API_REFERENCE.md            # Every endpoint, with curl examples
├── LOVABLE_PROMPT.md           # Paste into Lovable to scaffold the frontend
│
├── app/
│   ├── __init__.py             # Application factory
│   ├── config.py
│   ├── extensions.py           # db, migrate, jwt, cors, smorest_api, socketio, scheduler
│   ├── cli.py                  # `flask seed-roles`, `flask create-admin`
│   │
│   ├── core/
│   │   ├── security/           # jwt.py, password.py, permissions.py, roles.py
│   │   ├── middleware/         # auth, cors, error_handler, request_logger, rate_limit
│   │   └── utils/              # response, pagination, barcode, qr_code, receipt, ...
│   │
│   ├── models/                 # SQLAlchemy models (one file per table)
│   ├── schemas/                # marshmallow request/response schemas
│   ├── repositories/           # data-access layer
│   ├── services/               # business logic layer
│   ├── api/v1/                 # one folder per resource, each a flask-smorest Blueprint
│   ├── websocket/               # socket_server.py, handlers.py, events.py, rooms.py
│   ├── tasks/                   # scheduler.py + background jobs
│   └── docs/swagger.py          # registers all blueprints on the OpenAPI Api instance
│
├── uploads/                     # product images, barcodes, branding logo, exports
├── backups/                     # DB + full ZIP backups land here
├── logs/                        # app.log (rotating)
├── migrations/                  # Alembic migration history
└── tests/                       # pytest suite
```

---

## Quick start

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure secrets (edit .env — see next section)

export FLASK_APP=run.py
export FLASK_ENV=development

flask db init          # first time only — creates the migrations/ folder
flask db migrate -m "initial migration"
flask db upgrade

flask seed-roles        # creates admin/manager/cashier/inventory_clerk + permissions
flask create-admin      # creates the bootstrap admin user

python run.py            # starts the API + WebSocket server on :5000
```

Open **http://localhost:5000/docs** for Swagger UI. Log in with
`admin` / `admin123` (from `create-admin`'s defaults) and change the password
immediately via `POST /api/v1/auth/change-password`.

> `flask create-admin` accepts `--username`, `--password`, `--full-name`,
> `--email` flags if you want different defaults, e.g.
> `flask create-admin --username owner --password "S0meth1ngStrong!"`.

---

## Configuration (.env)

All configuration lives in `.env` at the project root (loaded automatically
via `python-dotenv`). Key variables:

| Variable | Purpose | Default |
|---|---|---|
| `FLASK_ENV` | `development` / `testing` / `production` | `development` |
| `SECRET_KEY` | Flask session/signing secret | *(change this)* |
| `JWT_SECRET_KEY` | JWT signing secret | *(change this)* |
| `DATABASE_URL` | SQLAlchemy URI. SQLite for dev, e.g. `postgresql://user:pass@host:5432/novapos` for prod | `sqlite:///novapos.db` |
| `JWT_ACCESS_TOKEN_EXPIRES_MINUTES` | Access token lifetime | `30` |
| `JWT_REFRESH_TOKEN_EXPIRES_DAYS` | Refresh token lifetime | `30` |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins | `http://localhost:3000,http://localhost:5173` |
| `UPLOAD_FOLDER` / `BACKUP_FOLDER` / `LOG_FOLDER` | Storage paths | `uploads` / `backups` / `logs` |
| `RATE_LIMIT_DEFAULT` | Default rate-limit string | `200 per hour` |
| `CHAPA_SECRET_KEY` | Chapa API secret key | *(unset = dev/placeholder mode)* |
| `CHAPA_WEBHOOK_SECRET` | Used to verify Chapa's webhook signature | *(unset = signature check skipped)* |
| `CHAPA_BASE_URL` | Override for testing against a mock server | `https://api.chapa.co` |

**Never commit real secrets.** `.env` is already in `.gitignore`.

---

## Running the server

Development (auto-reload, verbose errors):
```bash
export FLASK_ENV=development
python run.py
```

Production-style (no reloader/debugger, still fine for small deployments):
```bash
export FLASK_ENV=production
python run.py
```

Behind Gunicorn with the eventlet worker (recommended for real production,
single worker because Socket.IO needs sticky state — put a queue/Redis
backend in front if you need to scale horizontally):
```bash
gunicorn --worker-class eventlet -w 1 -b 0.0.0.0:5000 "run:app"
```

---

## Running tests

The test suite uses an in-memory SQLite database (`app.config.TestingConfig`)
so it never touches your real dev/prod database.

```bash
source venv/bin/activate
export FLASK_ENV=testing
python -m pytest tests/ -v
```

Run a single file or test:
```bash
python -m pytest tests/test_sales.py -v
python -m pytest tests/test_v2_features.py::test_checkout_session_cash_flow -v
```

Run with coverage (install `pytest-cov` first: `pip install pytest-cov`):
```bash
python -m pytest tests/ --cov=app --cov-report=term-missing
```

What's covered: auth/login, product + inventory CRUD and stock rules, the
full direct-checkout flow (including variants/units/discounts), void/refund
stock restoration, printer registration/discovery, product variants/units,
the customer-display checkout session (cash + Chapa placeholder flows),
session listing, the professional dashboard, bulk barcode generation +
PDF labels, full ZIP backup/verify, the refund search + approval workflow,
branding/tax config, and system health.

**Writing new tests:** `tests/conftest.py` provides an `app` fixture (fresh
DB + seeded roles + an `admin`/`admin123` user per test), a `client` fixture
(Flask test client), and an `auth_headers` fixture (already-logged-in bearer
token). Most new tests just need:
```python
def test_something(client, auth_headers):
    resp = client.post("/api/v1/products", json={...}, headers=auth_headers)
    assert resp.status_code == 201
```

---

## Database migrations

This project uses Flask-Migrate (Alembic). After changing any model:
```bash
flask db migrate -m "describe your change"
flask db upgrade
```
Always review the generated migration file under `migrations/versions/`
before applying it — autogenerate is good but not infallible (it won't
detect some column-type-only changes, for example).

To reset your local dev database from scratch:
```bash
rm -f instance/novapos.db     # SQLite dev DB lives under instance/ (Flask's
                                # relative-sqlite-path convention)
flask db upgrade
flask seed-roles
flask create-admin
```

---

## V1 feature summary

The original MVP backend, fully implemented:

- **Auth** — JWT login/refresh, role-based access control, permission checks.
- **Users & Roles** — CRUD, deactivate/reactivate, password reset, custom
  roles with a permission checklist.
- **Products & Categories** — full CRUD, barcode assignment, product images.
- **Inventory** — stock levels, restock, manual adjustment (with reason),
  full history log, low-stock listing.
- **Sales** — cart → checkout → stock deduction → payment → receipt →
  audit log, all in one transaction; void with automatic stock restoration.
- **Payments** — cash (with tendered/change), card, mobile money, wallet.
- **Refunds** — partial or full, per line item.
- **Customers** — profiles, purchase history, loyalty points.
- **Reports** — sales, profit, top products, inventory, by day/week/month/
  year or a custom range.
- **Dashboard** — today's revenue/sales/low-stock/top-sellers/recent activity.
- **Notifications** — low-stock alerts and general system notifications,
  pushed live over WebSocket.
- **Hardware registry** — generic device registration + heartbeat for
  scanners/printers/drawers/displays.
- **Backup & restore** — SQLite file backup/restore.
- **Settings** — key-value business settings.
- **Audit log** — who did what, when, to what.

## V2 feature summary

Everything added on top of V1 to make this a commercial-grade retail POS:

| # | Feature | Where |
|---|---|---|
| 1 | **Printer management** — profiles for USB/Bluetooth/network, discovery, default printer, test print, online/offline detection, auto-print on sale completion with offline retry | `/api/v1/printers` |
| 2 | **Customer display connection** — automatic discovery, pairing code + QR pairing, persistent reconnect | `/api/v1/pairing` |
| 3 | **Live checkout / customer payment selection** — draft checkout sessions, live cart streaming over WebSocket, customer picks cash/Chapa/offline, cashier confirms | `/api/v1/checkout` |
| 4 | **Chapa payments** — hosted checkout session creation, QR/link, webhook confirmation with signature verification | `/api/v1/payments/chapa/webhook` |
| 5 | **Product variants** — size/color/etc. with their own SKU, barcode, price, stock | `/api/v1/products/<id>/variants` |
| 6 | **Multiple units** — sell the same product in different units with a conversion ratio | `/api/v1/products/<id>/units` |
| 7 | **Advanced discounts** — percentage/fixed, product- or cart-level, with reason, fully audited | built into `/api/v1/sales` and `/api/v1/checkout` |
| 8 | **Bulk import/export** — products (CSV/Excel/JSON), customers & inventory (CSV) | `/api/v1/products/bulk/*`, `/api/v1/customers/export.csv`, `/api/v1/inventory/export.csv` |
| 9 | **Complete ZIP backup & restore** — DB + uploads + logs + settings/printers/devices, verified before restore | `/api/v1/backup/full`, `/verify`, `/restore-full` |
| 10 | **Receipt history** — search by receipt #, customer, cashier, date, payment method; reprint; PDF download | `/api/v1/sales/search`, `/api/v1/sales/<id>/receipt-pdf` |
| 11 | **Advanced barcode management** — manufacturer barcode scanning (duplicate-safe, configurable), bulk internal generation + printable Code128 PDF labels (3 sizes) | `/api/v1/products/<id>/barcodes/*` |
| 12 | **Professional refunds** — search by receipt/barcode/product barcode, human-readable "2 hours ago" purchase age, approval workflow | `/api/v1/refunds/*` |
| 13 | **Store branding** — name, logo, address, phone, email, tax number, shown wherever needed | `/api/v1/branding` |
| 14 | **Tax configuration** — enable/disable, rename, inclusive/exclusive, per-product override/exemption | `/api/v1/branding/tax`, `Product.is_tax_exempt` |
| 15 | **Stock alerts** — low-stock *and* distinct out-of-stock (critical) notifications; negative stock always rejected | built into inventory/variant services |
| 16 | **System health monitoring** — DB, printers, customer displays, CPU/memory/disk, last backup | `/api/v1/system/health` |
| 17 | **Categorized system logs** — auth/api/sales/inventory/payments/hardware/customer_display/backup/system | `/api/v1/system/logs` |
| 18 | **Session management** — active sessions, login history, force logout / revoke (enforced via JWT blocklist) | `/api/v1/sessions` |
| 19 | **Professional dashboard** — sales/inventory/payments/staff/hardware sections + recent activity + plain-language business insights | `/api/v1/dashboard/summary` |

Full request/response examples for every one of these: **[API_REFERENCE.md](./API_REFERENCE.md)**.

## V3 feature summary

V3 is a hardening/polish pass — fewer new modules, more focus on security,
performance, and the operational tools a real store needs day-to-day.

| # | Feature | Where |
|---|---|---|
| 1 | **Printer profiles** — receipt width, paper size, encoding, print density, auto-cut, logo printing, per-printer print history | `Printer` model fields, `/api/v1/printers/<id>/history` |
| 2 | **Customer display platform** — same pairing/discovery as V2, documented end-to-end for a real installation flow | `/api/v1/pairing/*` (see the Hardware section above) |
| 3 | **Device Manager** — unified device info (name/manufacturer/model/type/status/IP/last-seen), accessible to admin/manager/cashier/inventory clerk per permission | `/api/v1/hardware/devices`, `/api/v1/printers` |
| 4 | **Store branding** — logo upload now auto-resizes (max 512px, aspect preserved) and supports delete | `POST/DELETE /api/v1/branding/logo` |
| 5 | **Professional receipt engine** — variants, per-line discounts, QR + text verification code, refund policy footer, correct 58mm/80mm thermal widths, on both the plain-text and PDF receipts | `GET /api/v1/sales/<id>/receipt-text?paper_width_mm=58`, `/receipt-pdf` |
| 6 | **Unified API authentication** — every endpoint requires a Bearer JWT by default (enforced via a global OpenAPI security requirement); only genuinely public endpoints (login, receipt verification, branding read, webhooks, device/printer heartbeats, customer-display pairing/discovery/payment-selection) explicitly opt out. **Closed a real bug**: `/auth/register` was previously unauthenticated and could create accounts of any role — it now requires `users.manage`. | Swagger `/docs` shows the 🔒 Authorize button; see `app/config.py` `API_SPEC_OPTIONS` |
| 7 | **Gift cards & store credit** — issue, recharge, redeem (as a sale payment method), balance check, full transaction ledger; refunds can optionally issue store credit instead of cash back | `/api/v1/gift-cards/*`, `"method": "gift_card"` in `/api/v1/sales` |
| 8 | **Receipt & label designer (backend)** — stores drag-and-drop layouts as JSON templates with a settable default; the frontend owns the actual designer UI | `/api/v1/templates/receipts`, `/api/v1/templates/labels` |
| 9 | **Performance** — targeted indexes on `Sale.status/cashier_id/customer_id`, `SaleItem.sale_id/product_id`, `Payment.sale_id/method`, `AuditLog.entity_type/user_id`, `Notification.user_id`, `InventoryHistory.inventory_id`; in-process settings cache (invalidated on write) since settings are read on nearly every request | migrations, `app/services/settings_service.py` |
| 10 | **Transaction timeline** — full chronological event history per sale (creation, discounts, payments, printing, refunds, void), sourced from the audit log | `GET /api/v1/sales/<id>/timeline` |
| 11 | **Product history** — field-level change log (price, cost price, barcode, image, archive/restore), who changed it and when; stock changes still use the more detailed `InventoryHistory` | `GET /api/v1/products/<id>/history`, `POST /api/v1/products/<id>/restore` |
| 12 | **Favorite products** — pin/unpin per cashier, plus computed recently-sold and frequently-sold lists for quick-access buttons | `/api/v1/favorites/*` |
| 13 | **Keyboard shortcuts** — a frontend concern; see the recommended shortcut map in [LOVABLE_PROMPT.md](./LOVABLE_PROMPT.md) |  |
| 14 | **Global search** — one query across products, variants, categories, customers, users, and receipts | `GET /api/v1/search?q=...` |
| 15 | **Daily store closing report** — sales, profit, payment breakdown, refunds, discounts, cashier performance, inventory summary, hardware status; downloadable as PDF | `/api/v1/reports/daily-closing`, `/daily-closing/pdf` |
| 16 | **Notification center** — archive support added on top of V2's read/unread and severity, plus filter by type/severity | `POST /api/v1/notifications/<id>/archive`, `?type=&severity=` |
| 17 | **Saved draft sales** — checkout sessions already persist as `status="draft"` the moment they're created; a dedicated endpoint lists a cashier's recoverable carts | `GET /api/v1/checkout/drafts` |
| 18 | **Built-in calculator** — a frontend concern (no backend state needed); noted in the Lovable prompt |  |
| 19 | **Advanced product analytics** — top-selling, highest revenue/profit, fastest-growing, slow-moving, most-refunded, nearing depletion | `GET /api/v1/reports/product-analytics` |
| 20 | **Business calendar** — per-day aggregates (sales, revenue, refunds, inventory activity, new customers, backups) for a given month | `GET /api/v1/reports/calendar?year=&month=` |
| 21 | **Receipt verification** — every sale gets a public verification code (also encoded in the receipt's QR); anyone can confirm a receipt is genuine without logging in | `GET /api/v1/sales/verify/<code>` (no auth) |
| 22 | **Live activity feed** — every audited action (sales, refunds, product/inventory changes, logins, printer/customer-display/backup events, settings changes) now broadcasts to the dashboard in real time automatically | WebSocket event `activity:new` on the `dashboard` room |

---

## Security

- **Every endpoint requires a Bearer JWT by default.** This is enforced at
  the OpenAPI level (`API_SPEC_OPTIONS.security` in `app/config.py`), so
  Swagger UI shows a 🔒 Authorize button and marks protected operations
  automatically — there's no way to add a new endpoint and accidentally
  forget to think about auth, since the *absence* of `@jwt_required()` is
  what's now the exceptional, deliberate case.
- **Genuinely public endpoints** (and why each one is): `POST /auth/login`
  (that's how you get a token), `GET /branding` (the login page and customer
  display need store identity before authenticating), `GET /sales/verify/<code>`
  (customers verify receipts without an account), `POST /payments/chapa/webhook`
  (called by Chapa's servers), `POST /printers/heartbeat/<id>` and
  `POST /hardware/devices/heartbeat/<id>` (called by hardware/agents, not
  users), `GET /pairing/discover-terminals` and `POST /pairing/redeem` and
  `POST /checkout/<id>/customer-payment-method` (called by an unauthenticated
  customer display). Every one of these is marked `@blp.doc(security=[])` in
  its route file — grep for that if you're auditing.
- **Fixed in V3:** `POST /auth/register` was previously callable by anyone,
  with no authentication, and could create an account with *any* role
  including `admin`. It now requires a valid token with `users.manage`.
  If you deployed V1/V2 publicly, rotate credentials and check your user
  list for anything you don't recognize.
- **Session revocation is real**, not just client-side token deletion: every
  issued access token is tracked in `UserSession` with its JWT `jti`, and a
  `token_in_blocklist_loader` checks that table on every request. Force-logout
  via `/api/v1/sessions` actually invalidates the token server-side.
- Passwords are hashed with Werkzeug's PBKDF2 implementation (`core/security/password.py`) — never stored or logged in plaintext.
- Rate limiting is in-process (see Performance notes below) — for multi-worker
  production deployments, put a proper rate limiter (nginx, Cloudflare, or a
  Redis-backed limiter) in front instead of relying solely on this.

## Performance notes

- **Indexes**: added on the columns actually filtered/joined in hot paths —
  `Sale.status/cashier_id/customer_id`, `SaleItem.sale_id/product_id`,
  `Payment.sale_id/method`, `AuditLog.entity_type/user_id`,
  `Notification.user_id`, `InventoryHistory.inventory_id` — check
  `migrations/versions/` for the exact migration.
- **Settings cache**: `SettingsService.get_all()` is read on nearly every
  request (branding, tax, receipt formatting) but written rarely, so it's
  cached in-process with a version counter invalidated on every write. This
  is correct and free for a single-process/single-worker deployment. If you
  scale to multiple Gunicorn workers or multiple machines, replace the
  module-level dict with a shared cache (Redis) so a setting change on one
  worker is visible to the others — otherwise workers can serve stale
  settings until they happen to restart.
- **Pagination is mandatory** on every list endpoint (`page`/`per_page`,
  capped at 100 per page) — there's no "get everything" endpoint that can
  accidentally return an unbounded result set.
- **Report/analytics queries** use SQL aggregation (`GROUP BY`/`SUM`) rather
  than pulling rows into Python and summing — see `report_service.py` for
  the pattern to follow if you add new reports.
- **Background jobs** (nightly backup, notification cleanup, daily report
  snapshot) run via APScheduler in-process; for a busier deployment, move
  these to a real task queue (Celery/RQ) so they don't compete with request
  handling on the same process.
- For real production load with heavy WebSocket use, use a Socket.IO-aware
  message queue (Redis adapter) if you need both multiple workers *and*
  realtime — see Deployment notes below.

---

## Connecting & testing hardware

A cloud/server backend cannot directly drive USB, Bluetooth, or discover
devices on the local network by itself — that requires OS-level access that
only something running *on the till machine* has. NovaPOS's hardware
features are therefore split into two halves:

- **Backend (this repo):** stores printer/device profiles, decides what's
  "default," receives heartbeats, and dispatches print jobs / pairing over
  WebSocket.
- **Local agent (small helper app or the cashier browser tab with USB/Web
  Bluetooth APIs):** performs the actual USB/Bluetooth/mDNS scanning, talks
  to the physical printer driver, and reports status back to the backend.

This is normal architecture for browser-based POS systems (Square, Shopify
POS, etc. all work this way) — it's not a limitation specific to this build.

### Receipt printers

**1. Register a printer profile** (usually done once per till, either
manually or by your local agent posting what it found):
```bash
curl -X POST http://localhost:5000/api/v1/printers \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "name": "Front Counter",
    "connection_type": "network",
    "identifier": "192.168.1.50:9100",
    "ip_address": "192.168.1.50",
    "manufacturer": "Epson",
    "model": "TM-T20III",
    "profile_type": "receipt"
  }'
```
`connection_type` is one of `usb | bluetooth | network`. For USB/Bluetooth,
`identifier` should be whatever stable string your local agent can use to
address the device again (a USB serial number, or a Bluetooth MAC address).

**2. Or let a discovery scan populate it.** If you build a local agent (or
a browser page using the WebUSB/Web Bluetooth APIs) that can enumerate
printers, have it POST what it found:
```bash
curl -X POST http://localhost:5000/api/v1/printers/discover \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"discovered": [
    {"name": "USB Printer", "connection_type": "usb", "identifier": "usb-0001",
     "manufacturer": "Epson", "model": "TM-T20"}
  ]}'
```
This upserts each entry (existing identifiers get their status refreshed to
`online`; new ones get created) and returns the full saved-printer list,
including any previously-saved printers *not* in this scan (which you can
treat as possibly offline).

**3. Set it as default:**
```bash
curl -X POST http://localhost:5000/api/v1/printers/1/set-default -H "Authorization: Bearer $TOKEN"
```

**4. Test it.** This sends a `print:job` WebSocket event (room:
`pos_terminals`) with a small test payload — your local agent should be
listening for this event and actually send it to the printer:
```bash
curl -X POST http://localhost:5000/api/v1/printers/1/test-print -H "Authorization: Bearer $TOKEN"
```
Minimal Node/JS agent sketch:
```js
const io = require("socket.io-client");
const socket = io("http://localhost:5000");
socket.emit("join", { room: "pos_terminals" });
socket.on("print:job", async ({ printer_id, connection_type, content }) => {
  // connection_type === "network" -> open a raw TCP socket to the printer's
  // IP:port and write `content` (or ESC/POS bytes you build from it);
  // "usb"/"bluetooth" -> hand off to your OS printer driver / node-thermal-printer.
  console.log(`Print job for printer #${printer_id}:\n${content}`);
});
```

**5. Keep status fresh.** Have your agent call the (unauthenticated)
heartbeat endpoint every minute or so per printer so the backend can tell
online from offline (used in `/api/v1/system/health` and the dashboard):
```bash
curl -X POST http://localhost:5000/api/v1/printers/heartbeat/usb-0001 \
  -H "Content-Type: application/json" -d '{"paper_status":"ok"}'
```

**6. What happens automatically:** every completed sale
(`POST /api/v1/sales` or a finished checkout session) automatically calls
the default printer. If it hasn't heartbeated in the last 5 minutes, the
sale still completes, but the cashier gets an `printer_offline` notification
and can retry (`POST /api/v1/sales/{id}/print`) or pick a different saved
printer (`{"printer_id": <other_id>}` in the same call).

### Customer display

**1. Register the till as a POS terminal device** (once, e.g. at setup time):
```bash
curl -X POST http://localhost:5000/api/v1/hardware/devices \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Register 1", "device_type": "pos_terminal", "identifier": "term-001"}'
```

**2. Pick a connection method** (the display tries these in order, exactly
as described in the product spec):
- **Automatic discovery:** `GET /api/v1/pairing/discover-terminals` (no
  auth) lists POS terminals that have sent a heartbeat/login in the last 5
  minutes — show these as tap-to-connect options.
- **Pairing code / QR code:** on the till, generate a code:
  ```bash
  curl -X POST http://localhost:5000/api/v1/pairing/generate-code \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -d '{"terminal_id": 1, "server_address": "http://192.168.1.10:5000"}'
  ```
  This returns `{ code, expires_at, qr_code_base64 }` — display the code
  and/or QR on the till screen. On the customer display, either type the
  code or scan the QR, then redeem it:
  ```bash
  curl -X POST http://localhost:5000/api/v1/pairing/redeem \
    -H "Content-Type: application/json" \
    -d '{"code": "420541", "display_identifier": "tablet-abc123", "display_name": "Window Display"}'
  ```
  The response includes `websocket_room: "customer_displays"` — the display
  should connect to Socket.IO and `emit("join", {room: "customer_displays"})`.
- **Manual server address:** just point the display's Socket.IO client at
  the backend URL directly — no API call needed.

**3. Persistent reconnect:** the display should store its own
`display_identifier` locally and simply reconnect its WebSocket + re-join
the `customer_displays` room on every app start — no need to re-redeem a
pairing code each time.

**4. What the display shows:** listen for `checkout:update` (live cart while
the cashier is ringing items up — render product list/qty/price/discounts/
tax/running total), `customer:payment_selected` isn't for the display itself
(that's the event *sent to the cashier* after the display calls
`customer-payment-method`), and `payment:confirmed` (show a thank-you
screen). When there's no active sale, show your idle/welcome screen (store
logo/name from `GET /api/v1/branding`, current time, optional promos).

**5. Customer payment selection** (called *by* the display, no auth):
```bash
curl -X POST http://localhost:5000/api/v1/checkout/{sale_id}/customer-payment-method \
  -H "Content-Type: application/json" -d '{"method": "chapa"}'
```
For Chapa, render the returned `qr_code_base64` PNG so the customer can scan
it, or open `checkout_url` directly if the display has a browser.

### Cash drawer

Register it as a device (`device_type: "cash_drawer"`), then:
```bash
curl -X POST http://localhost:5000/api/v1/hardware/devices/1/open-drawer -H "Authorization: Bearer $TOKEN"
```
This emits a `hardware:cash_drawer_open` WebSocket event to the
`pos_terminals` room — your till's local agent (which is wired to the
drawer, usually via the receipt printer's kick-out port) listens for this
and triggers the actual open signal.

---

## Chapa payment integration

1. Get your secret key and set up a webhook URL in your Chapa dashboard
   pointing at `https://yourdomain.com/api/v1/payments/chapa/webhook`.
2. Set in `.env`:
   ```
   CHAPA_SECRET_KEY=CHASECK_...
   CHAPA_WEBHOOK_SECRET=...
   ```
3. Without these set, the backend runs in a **placeholder mode**: it still
   returns a fake `checkout_url`/QR and lets you exercise the entire flow
   (including simulating a webhook call yourself) without hitting Chapa's
   real API — useful for frontend development before you have live
   credentials.
4. The flow: customer picks "Chapa" on the display →
   `POST /api/v1/checkout/{id}/customer-payment-method` creates a pending
   `Payment` row + hosted session → customer pays → Chapa calls your webhook
   → the backend re-verifies the transaction directly with Chapa (never
   trusts the webhook payload alone) → the sale is finalized, stock
   deducted, and the receipt auto-printed.

---

## Backup & restore

- **Quick DB-only backup:** `POST /api/v1/backup` (SQLite file copy).
- **Complete backup:** `POST /api/v1/backup/full` — a single ZIP containing
  the database, every uploaded file (product images, barcode/label images,
  branding logo), the logs folder, and a JSON export of settings/printers/
  registered devices. Download it with
  `GET /api/v1/backup/{id}/download`.
- **Restoring:** always verify first —
  `POST /api/v1/backup/verify` (multipart `file`) checks the archive is a
  valid ZIP with our manifest before you commit to restoring. Then
  `POST /api/v1/backup/restore-full` (multipart `file`) extracts and
  restores everything.
- Nightly automatic backups run at 02:00 server time via APScheduler (see
  `app/tasks/backup_tasks.py`) — these are the quick DB-only kind; schedule
  full ZIP backups yourself (e.g. an external cron hitting `/api/v1/backup/full`)
  if you want those automated too.

---

## WebSocket integration guide

Connect Socket.IO to the same host/port as the REST API — no separate
server or port. See **[API_REFERENCE.md](./API_REFERENCE.md#websocket-events-socketio)**
for the full event table. Quick example:

```js
import { io } from "socket.io-client";

const socket = io("http://localhost:5000");
socket.emit("join", { room: "pos_terminals" }); // or "dashboard" / "customer_displays"

socket.on("sale:created", (sale) => { /* refresh dashboard */ });
socket.on("notification:new", (n) => { /* show toast, bump bell count */ });
socket.on("print:job", ({ content, connection_type }) => { /* send to printer driver */ });
```

---

## Roles & permissions

Seeded by `flask seed-roles`:

| Role | Permissions |
|---|---|
| `admin` | `*` (everything) |
| `manager` | products/categories/inventory/sales/customers manage, `reports.view`, `dashboard.view`, `refunds.manage`, `settings.manage`, `users.view` |
| `cashier` | `sales.create`, `sales.view`, `products.view`, `customers.view`/`manage`, `payments.create`, `refunds.create`, `dashboard.view` |
| `inventory_clerk` | `products.view`/`manage`, `inventory.manage`/`view`, `categories.view`, `dashboard.view` |

Permissions are dotted strings (`"resource.action"`); manage them at runtime
via `/api/v1/roles` — no code changes or redeploys needed to adjust who can
do what.

---

## Building a frontend

Two options, both documented:

1. **[LOVABLE_PROMPT.md](./LOVABLE_PROMPT.md)** — paste directly into
   [Lovable](https://lovable.dev) to scaffold a complete React admin +
   cashier UI wired to this API.
2. **[API_REFERENCE.md](./API_REFERENCE.md)** — for any other frontend
   (custom React app, mobile app, etc.), every endpoint with example
   requests/responses.

Set your frontend's API base URL to wherever this backend is running, and
remember to add its origin to `CORS_ORIGINS` in `.env`.

---

## Deployment notes

- Run behind `gunicorn --worker-class eventlet -w 1 -b 0.0.0.0:5000 "run:app"`
  (single worker — Socket.IO needs sticky sessions; put a message-queue-backed
  Socket.IO adapter in front if you need multiple workers/instances).
- Point `DATABASE_URL` at PostgreSQL for production:
  `postgresql://user:pass@host:5432/novapos`.
- Set strong, unique `SECRET_KEY` / `JWT_SECRET_KEY` values — don't reuse the
  dev placeholders.
- Set real `CHAPA_SECRET_KEY` / `CHAPA_WEBHOOK_SECRET` for live payments.
- Put a reverse proxy (nginx) in front for TLS termination and to serve
  `/uploads` as static files efficiently.
- Schedule off-box copies of `/api/v1/backup/full` ZIPs (e.g. sync `backups/`
  to S3/Cloud Storage) — local backups don't protect against server loss.

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `401 Unauthorized` on every request | Missing/expired `Authorization: Bearer` header — re-login or hit `/api/v1/auth/refresh`. |
| `403` "You do not have permission..." | The logged-in user's role lacks that permission — check `/api/v1/roles` or log in as `admin`. |
| `429 Too Many Requests` on login | The in-memory rate limiter (60/min per IP+endpoint) tripped — wait a minute, or raise the limit in `app/api/v1/auth/routes.py` for local dev/testing. |
| Sale fails with "Insufficient stock" | Expected behavior — check `/api/v1/inventory/product/{id}` for real-time stock before retrying. |
| Printer always shows "offline" | Your local agent isn't heartbeating (`POST /api/v1/printers/heartbeat/{identifier}`) at least every ~5 minutes, or isn't listening for `print:job` at all. |
| Chapa webhook never fires locally | Chapa can't reach `localhost` — use a tunnel (ngrok, Cloudflare Tunnel) during development and set that URL as your webhook in the Chapa dashboard. |
| `flask db migrate` detects no changes after editing a model | Make sure the model is imported in `app/models/__init__.py` — Alembic only sees models that get imported. |
| SQLite "database is locked" under load | SQLite is fine for a single-till dev setup; for multi-terminal production, switch `DATABASE_URL` to PostgreSQL. |
| Tests fail with `KeyError: 'data'` on login | Usually the rate limiter tripped across tests in the same process — `tests/conftest.py` already resets it per test; make sure any new test file doesn't bypass that fixture. |
| Changed a setting via the API but an old value is still returned elsewhere | The in-process settings cache (see Performance notes) is per-worker; if you're running multiple Gunicorn workers, only the worker that handled the write sees the change immediately — restart other workers or add a shared cache for multi-worker deployments. |
| `POST /api/v1/auth/register` returns 401 | This is intentional as of V3 — it now requires a valid token with `users.manage` (previously it was an unauthenticated security hole). Log in as an admin/manager first, or use `POST /api/v1/users` instead. |
| A new endpoint I added isn't showing the 🔒 lock in Swagger / isn't actually protected | Check that the method has `@jwt_required()`; the global `security` default only documents the *expectation* that the endpoint needs a token — it doesn't add the auth check itself. If it's meant to be public, add `@blp.doc(security=[])` so Swagger reflects that honestly. |

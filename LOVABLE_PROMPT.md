# NovaPOS Frontend — Lovable Prompt

Copy everything below into Lovable to start the build. It explains exactly
how the backend works (so the AI doesn't guess at auth/data shapes) and then
describes every screen in detail. It's long — you can paste it in one shot,
or split at the `## Screens` heading and paste the architecture section
first, then build screens one at a time in follow-up prompts.

---

## Prompt

Build **NovaPOS**, a professional, enterprise-grade Point-of-Sale web
application frontend for a retail store. This is a **frontend only** — a
complete Flask REST + WebSocket API already exists and is the single source
of truth for all data. Never invent a backend, never use localStorage as a
database, never fabricate data shapes — everything below describes the real
API exactly as implemented.

### Tech stack

- React + TypeScript, Tailwind CSS, shadcn/ui components, lucide-react icons.
- React Router for navigation, React Query (TanStack Query) for all API data
  fetching/caching/mutations.
- socket.io-client for realtime updates.
- Store the API base URL in one config value (e.g. `VITE_API_BASE_URL`,
  default `http://localhost:5000`).

---

## How the backend works (read this before building anything)

### Versioning & base path
Every endpoint is under `{API_BASE}/api/v1/...`. There is no unversioned API.

### Response envelope — ALWAYS this shape
```json
{ "success": true, "message": "Human-readable message", "data": { ... }, "meta": { ... } }
```
On error:
```json
{ "success": false, "message": "Human-readable error", "errors": {...}, "error_code": "SOME_CODE" }
```
`meta` only appears on paginated list endpoints:
`{ "page": 1, "per_page": 20, "total_items": 143, "total_pages": 8, "has_next": true, "has_prev": false }`.

Build **one** shared API client that:
1. Prefixes every call with the base URL.
2. Attaches `Authorization: Bearer <access_token>` automatically.
3. Unwraps `data` on success and throws/returns the `message` on failure so
   every screen can show the *exact* backend message in a toast — the
   backend already writes these to be user-friendly (e.g. "Insufficient
   stock for 'Cola 330ml'. Available: 3, requested: 5." — show that
   verbatim, don't replace it with a generic "Something went wrong").
4. On a 401, tries `POST /api/v1/auth/refresh` with the refresh token once;
   if that also 401s, clears tokens and redirects to `/login`.

### Authentication & authorization
- `POST /api/v1/auth/login` with `{username, password}` → `{access_token, refresh_token, user}`.
  Optional header `X-Terminal-Id: <device_id>` associates the session with a registered POS terminal.
- **Every single endpoint requires the Bearer token by default** — this is
  enforced backend-side via a global OpenAPI security policy, not just
  convention. A short, explicit list of endpoints are intentionally public
  (see "Public endpoints" below) — everything else will 401 without a token.
- The user's role and permission list are embedded in the JWT and also
  returned from `GET /api/v1/auth/me`. Permissions are dotted strings like
  `"products.manage"`, `"sales.create"`, `"refunds.manage"`; an admin has the
  wildcard `"*"` which grants everything. Build one `hasPermission(perm)`
  helper and use it to hide/disable actions and whole sidebar sections —
  don't just rely on the backend rejecting the request, the UI should never
  offer an action the user can't perform.
- Seeded default roles: `admin` (everything), `manager` (most business
  operations + settings, not user/role management beyond viewing),
  `cashier` (sales, refunds requests, customer view/create, dashboard view),
  `inventory_clerk` (products + inventory management, view-only elsewhere).
- **Session management is real**, not cosmetic: every login creates a
  server-side session row; an admin can force-logout any session
  (`POST /api/v1/sessions/<id>/revoke` or `/user/<id>/force-logout`) and it
  actually invalidates that token on the next request (401), so build the
  Sessions admin screen expecting real effect, and handle a sudden 401
  gracefully (redirect to login with a "your session was ended" message).

### Public endpoints (no token required) — build these UI flows knowing they're unauthenticated
- `POST /api/v1/auth/login`
- `GET /api/v1/branding` — used on the login page and by the customer display
- `GET /api/v1/sales/verify/<verification_code>` — public receipt authenticity check
- `POST /api/v1/payments/chapa/webhook` — not called by your frontend at all
- `POST /api/v1/printers/heartbeat/<identifier>` and `POST /api/v1/hardware/devices/heartbeat/<identifier>` — called by hardware agents, not your frontend
- `GET /api/v1/pairing/discover-terminals`, `POST /api/v1/pairing/redeem` — called by the customer display, not the cashier/admin app
- `POST /api/v1/checkout/<sale_id>/customer-payment-method` — called by the customer display

### Pagination, search, sorting
List endpoints accept `?page=1&per_page=20` (capped at 100). Many also
accept `?search=...` (products search name/sku/barcode) and
`?sort_by=name&sort_dir=asc`. Always read `meta` for pagination controls —
never assume a list response is the complete dataset.

### Realtime (Socket.IO)
Connect once after login to the same host/port as the REST API. Join rooms
based on the current screen/role:
```js
socket.emit("join", { room: "dashboard" });        // admin/manager views
socket.emit("join", { room: "pos_terminals" });    // cashier screen
socket.emit("join", { room: "customer_displays" }); // (not built here, but the events exist)
```
Events to wire up:
- `sale:created` (dashboard, pos_terminals) — refresh relevant lists/stats.
- `notification:new` (dashboard) — bump the bell badge, show a toast.
- `activity:new` (dashboard) — append to the live activity feed, no refetch needed.
- `checkout:update` (customer_displays) — not relevant to this frontend, but don't break if received.
- `customer:payment_selected` (pos_terminals) — the cashier's checkout-session screen updates to show what the customer picked.
- `payment:confirmed` (pos_terminals) — checkout-session sale is done; show the receipt.
- `print:job` (pos_terminals) — if you're simulating a print agent in-app for demo purposes, log/display it; otherwise ignore.
- `hardware:cash_drawer_open` (pos_terminals) — purely informational.

### Error handling philosophy
Every mutation shows a toast on success (`message` field) and a toast with
the exact error `message` on failure. 409 = conflict (e.g. insufficient
stock, duplicate SKU) — show inline where possible, not just a toast. 422 =
validation — map `errors` to form fields when the shape allows it. 404/403 —
short, clear message + safe fallback navigation.

---

## Global layout

Left sidebar (collapsible), top bar with store branding (`GET /api/v1/branding`
— call this even on the login page, no auth needed), current user menu,
global search box (see Global Search screen), and a notification bell.
Sidebar sections — hide any the current role/permissions can't access:

**Dashboard · Point of Sale · Products** (Categories, Variants, Units,
Barcodes, Import/Export, Product History as sub-views) **· Inventory ·
Customers · Gift Cards · Sales History · Refunds · Reports** (Sales/Profit/
Top Products/Inventory/Daily Closing/Product Analytics/Business Calendar)
**· Hardware** (Printers, Customer Displays, Device Manager) **·
Notifications · Users & Roles · Settings** (Branding, Tax, Receipt & Label
Designer, Backup, System Health, System Logs, Sessions).

Aesthetic: confident whitespace, a primary brand color pulled from store
branding if available (fallback professional indigo/slate), crisp tables,
clear status badges (green=online/completed, amber=warning/pending,
red=offline/critical/error).

---

## Screens

### 1. Login page
Centered card: store logo or name, username + password, "Sign in". On 401
show "Invalid username or password" — don't leak whether the username
existed.

### 2. Dashboard (`GET /api/v1/dashboard/summary`)
Render each top-level key as its own section:
- **`sales`**: today's sales count, revenue, estimated profit, average sale
  value, refund summary — stat cards.
- **`inventory`**: total/active products, inventory value, low-stock count,
  out-of-stock count.
- **`payments`**: a small chart of cash/chapa/offline/gift_card totals today.
- **`staff`**: active cashier count + sales-by-cashier leaderboard.
- **`hardware`**: printer + customer-display online/offline counts.
- **`recent_activity`**: timeline list (action, user, timestamp).
- **`insights`**: an array of ready-made human-readable strings (e.g.
  "Sales increased by 15% compared to yesterday.") — render as a highlighted
  banner/list, don't try to parse or recompute them.
Also render a **live activity feed** panel fed by the `activity:new`
WebSocket event (prepend new entries, no refetch) — this is a distinct,
continuously-updating list separate from the one-time `recent_activity`
snapshot in the summary payload.

### 3. Point of Sale (cashier screen) — the most important screen
Two-panel layout.

**Left — product search/grid.** A search box that doubles as a barcode
scanner input (scanners type + Enter): on Enter, try
`GET /api/v1/products/barcode/{code}` first; if that 404s, fall back to
`GET /api/v1/products?search=...`. Show product cards (image, name, price,
stock). A **Favorites bar** above the grid: `GET /api/v1/favorites` for
pinned quick-access buttons, plus tabs for `GET /api/v1/favorites/recently-sold`
and `/frequently-sold` — clicking any adds it to the cart. Long-press or a
small pin icon on any product card calls `POST /api/v1/favorites/{product_id}`.
If a product has variants, show a variant picker sheet before adding to
cart; if it has alternate units, offer a unit selector.

**Right — the running cart.** Line items with quantity steppers, a per-line
discount button (dialog: percentage or fixed amount, optional reason —
maps to `discount_type`/`discount_value`/`discount_reason` on the item), a
cart-level discount field (`discount_amount`/`discount_reason` on the sale),
subtotal/tax/discount/total summary, and a customer picker (search
`/api/v1/customers`, or "walk-in"). Include a small **floating calculator**
button (pure frontend component, no API calls — a basic four-function
calculator overlay for quick math during checkout).

**Checkout — two modes:**
1. **Quick checkout**: a payment panel — cash (amount tendered → auto
   change), card, offline, or **gift card** (a code input +
   `GET /api/v1/gift-cards/{code}/balance` to show available balance before
   confirming). Calls `POST /api/v1/sales` with the full cart in one shot.
   Show a receipt preview after, with "Reprint"
   (`POST /api/v1/sales/{id}/print`, optionally choosing a different saved
   printer if the default is offline) and "Download PDF"
   (`GET /api/v1/sales/{id}/receipt-pdf`) actions.
2. **Customer-display checkout**: `POST /api/v1/checkout/start`, then
   `PUT /api/v1/checkout/{id}/items` on every cart change (debounce ~300ms).
   Listen for `customer:payment_selected` — show a "waiting for customer"
   state, then Confirm/Reject buttons for cash
   (`confirm-cash`/`reject-cash`), a Confirm button + reference field for
   offline (`confirm-offline`), or a "waiting for payment..." spinner for
   Chapa (the backend's webhook finalizes it automatically — listen for
   `payment:confirmed`).

**Draft recovery banner:** on POS screen load, call
`GET /api/v1/checkout/drafts?mine_only=true` — if any exist, show a banner
("You have an unfinished sale — Resume?") so a browser crash/refresh never
silently loses a cart.

**Keyboard shortcuts** (implement these as global key handlers on this
screen): `F1` focus search, `F2` go to checkout/payment panel, `F3` open
customer picker, `F4` open discount dialog for the selected line/cart, `F5`
hold current sale (save as draft, clear cart), `F6` resume a held sale
(open the drafts list), `F7` open the refund flow, `Ctrl+S` complete the
current sale, `Ctrl+P` reprint the last receipt, `Delete` remove the
selected cart line, `Esc` cancel/close the current dialog. Show a small "?"
help overlay listing these.

### 4. Products
Table: search, category filter, active/inactive filter, stock column,
pagination. Row actions: edit, archive (`DELETE /api/v1/products/{id}` —
soft-delete), restore (`POST /api/v1/products/{id}/restore` — only shown
for archived products), manage variants/units/barcodes, upload image, view
history.
- **Create/edit form**: SKU, barcode (+ "generate" button), name,
  description, price, cost price, tax rate, tax-exempt toggle, category,
  unit, initial stock, low-stock threshold, image upload.
- **Variants tab** (`/api/v1/products/{id}/variants`): table (name/SKU/
  barcode/price/stock), add/edit/deactivate, quick restock action
  (`POST .../stock`).
- **Units tab** (`/api/v1/products/{id}/units`): table (unit name/conversion
  ratio/price/barcode), add/edit/deactivate.
- **Barcodes tab** (`/api/v1/products/{id}/barcodes`): a "scan manufacturer
  barcode" input (`.../scan`), and a "Bulk generate" panel — quantity +
  batch label (`.../bulk-generate`), then a checklist of generated codes to
  print as a PDF label sheet (`.../print-labels`, choose label size
  small/medium/large).
- **Product History tab** (`GET /api/v1/products/{id}/history`): a
  chronological log of price/cost/barcode/image/archive/restore changes,
  each showing old → new value and who changed it.
- **Import/Export**: buttons for `/bulk/export.csv`, `/export.xlsx`,
  `/export.json`, and an import dialog (`POST /bulk/import`) showing the
  resulting `{created, updated, errors}` summary.

### 5. Categories
Simple hierarchical list (supports `parent_id`), create/edit/delete.

### 6. Inventory
Table of stock levels, low-stock filter, restock/adjust actions (quantity +
reason — clearly warn if an adjustment would go negative, the backend
rejects it with a 409), threshold editor, per-product stock history
timeline, CSV export.

### 7. Customers
Table with search, create/edit, purchase history, loyalty points. On a
customer's detail page, show their **Gift Cards** section too
(`GET /api/v1/gift-cards/customer/{id}`).

### 8. Gift Cards
A dedicated management screen: search/list, "Issue new gift card" (amount,
optional customer, optional expiry), each card's detail view shows balance
and full transaction ledger (`.../transactions`), with recharge and manual
redeem actions. Distinguish `card_type` "gift_card" vs "store_credit"
visually (store credit is usually issued automatically from a refund, not
purchased).

### 9. Sales History / Receipts
Search form (`GET /api/v1/sales/search`): receipt number, customer, cashier,
date range, payment method. Row actions: View (full detail incl. a
**Timeline tab** — `GET /api/v1/sales/{id}/timeline`, a chronological event
list), Reprint, Download PDF, Refund, Void (permission-gated, reason
prompt). The detail view should show the `verification_code` and let the
user view/copy the same verification URL a customer could use.

### 10. Refunds
"Find sale to refund" search (receipt number / receipt barcode / product
barcode — `GET /api/v1/refunds/search`) showing matched sale(s) with
human-readable purchase age ("3 days ago"), customer, cashier, payment
method, and each item's refundable quantity. Cashier selects items +
quantities, optional reason, and either "Refund now" (direct,
`POST /sale/{id}`) or "Request approval" (`POST /sale/{id}/request`) —
show which one based on permissions. Add an **"Issue as store credit"**
toggle (`as_store_credit: true`) instead of cash back, when the sale has a
linked customer. A manager queue shows pending requests with
Approve/Reject buttons. Include a refund history table.

### 11. Reports
Tabbed or period-selector-driven views:
- **Sales / Profit / Top Products / Inventory** (as before — period
  selector: today/week/month/year/custom range).
- **Daily Closing Report** (`GET /api/v1/reports/daily-closing?date=`): a
  formatted end-of-day summary (sales, profit, payment breakdown, refunds,
  discounts, cashier performance, inventory summary, hardware status) with
  a "Download PDF" button (`/daily-closing/pdf`).
- **Product Analytics** (`GET /api/v1/reports/product-analytics`): tabs or
  cards for top-selling, highest revenue, highest profit, fastest-growing,
  slow-moving, most-refunded, and nearing-depletion — bar charts work well.
- **Business Calendar** (`GET /api/v1/reports/calendar?year=&month=`): a
  month grid where each day cell shows a tiny sales/revenue indicator;
  clicking a day could deep-link into the daily closing report for that date.

### 12. Hardware
- **Printers tab**: saved printers with connection-type badge, online/
  offline status, paper status, default star. "Scan for printers"
  (`/api/v1/printers/discover` — note this reflects whatever a local agent
  reports, not an in-browser scan). Actions: set default, rename, test
  print, delete, and a **History** view per printer
  (`GET /api/v1/printers/{id}/history` — job type, status, timestamp).
  Explain via helper text that a local agent handles actual USB/Bluetooth
  communication.
- **Customer Displays tab**: paired displays (`/api/v1/hardware/devices`
  filtered to `device_type=customer_display`), "Generate pairing code"
  (shows the 6-digit code + QR from the base64 payload, with an expiry
  countdown).
- **Device Manager tab**: a unified table of all devices (any type) with
  name/manufacturer/model/type/status/IP/last-seen — this is the superset
  view combining printers + generic devices; make it accessible (with
  view-only actions) to inventory clerks too, per the permission model.

### 13. Notifications
Full notification center: filterable by type and severity
(`?type=&severity=`), unread/all/archived tabs, mark-as-read, archive
(`POST /api/v1/notifications/{id}/archive`) swipe/button action. Severity
badges: info/warning/critical.

### 14. Users & Roles (admin only)
Users: create/edit/deactivate/reactivate/reset-password/assign-role. Roles:
create/edit roles with permission checkboxes grouped by resource
(products.*, sales.*, inventory.*, etc.).

### 15. Settings
- **Branding**: name, address, phone, email, website, tax number, logo
  upload (auto-resized server-side) with delete option and live preview of
  where it appears (login/receipt/customer display mockup thumbnails).
- **Tax**: enable/disable, rename (e.g. "VAT"), default rate,
  prices-include-tax toggle.
- **Receipt & Label Designer**: list of saved templates
  (`/api/v1/templates/receipts` and `/labels`), each with a name, paper
  width/label size, and a JSON `layout`. Build an actual drag-and-drop
  canvas here — draggable elements like Logo, Store Name, Items Table,
  Totals, QR Code, Footer Text, Barcode, Price, SKU — and serialize the
  resulting element list as the `layout` JSON on save. Let the user set a
  template as default (`/set-default`).
- **Backup & Restore**: list with size/date/status, "Create full backup"
  (`POST /backup/full`), download, and an upload → verify → restore flow
  with an explicit confirmation step (this is destructive).
- **System Health**: DB/API/printers/customer-displays status, CPU/memory/
  disk bars, last backup — auto-refresh every 30s.
- **System Logs**: filterable by category (authentication, api, sales,
  inventory, payments, hardware, customer_display, backup, system) and severity.
- **Sessions**: active sessions (user, device info, IP, last seen),
  force-logout per session or per user, login history.

### 16. Global Search
A command-palette-style search (e.g. Cmd/Ctrl+K to open) hitting
`GET /api/v1/search?q=...`, grouping results by type (products, variants,
categories, customers, users, sales) with instant navigation to the
matching detail page on click.

---

## What NOT to build

Don't implement actual USB/Bluetooth/network printer discovery or driver
communication in the browser, and don't build the physical customer-display
app itself — those are out of scope for this frontend. The UI only calls
the discovery/pairing/print endpoints and reflects their results; a
separate local agent (or the customer-display's own app, built elsewhere)
handles the hardware side. The floating calculator and keyboard shortcuts
described above are the only "no backend call needed" pieces — everything
else should be wired to a real endpoint from the list above.

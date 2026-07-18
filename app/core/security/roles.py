"""System role constants.

Roles are also stored as rows in the `roles` table (so they can carry
permission sets and be extended), but these constants give code a
single source of truth for the built-in role names.
"""

ADMIN = "admin"
MANAGER = "manager"
CASHIER = "cashier"
INVENTORY_CLERK = "inventory_clerk"

ALL_ROLES = [ADMIN, MANAGER, CASHIER, INVENTORY_CLERK]

# Default permission sets seeded for each built-in role at bootstrap time.
DEFAULT_ROLE_PERMISSIONS = {
    ADMIN: ["*"],
    MANAGER: [
        "products.manage", "categories.manage", "inventory.manage",
        "sales.manage", "sales.view", "customers.manage", "reports.view",
        "dashboard.view", "notifications.view", "users.view",
        "refunds.manage", "settings.manage",
    ],
    CASHIER: [
        "sales.create", "sales.view", "products.view", "customers.view",
        "customers.manage", "dashboard.view", "payments.create",
        "refunds.create",
    ],
    INVENTORY_CLERK: [
        "products.view", "products.manage", "inventory.manage",
        "inventory.view", "categories.view", "dashboard.view",
    ],
}

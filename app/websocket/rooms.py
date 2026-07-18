"""
Room naming conventions for targeted broadcasts.

Rooms let us push updates only to the clients that care:
- dashboard: React admin dashboards
- pos_terminals: cashier UIs
- customer_displays: Raspberry Pi customer-facing screens
"""
DASHBOARD_ROOM = "dashboard"
POS_TERMINALS_ROOM = "pos_terminals"
CUSTOMER_DISPLAYS_ROOM = "customer_displays"

ALL_ROOMS = [DASHBOARD_ROOM, POS_TERMINALS_ROOM, CUSTOMER_DISPLAYS_ROOM]


def device_room(device_id):
    return f"device:{device_id}"

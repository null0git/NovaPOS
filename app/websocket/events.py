"""
Event emitters called from the service layer to push realtime updates.

Kept separate from handlers.py: handlers.py reacts to client socket events,
this module is the outbound API services call into.
"""
from app.extensions import socketio
from app.websocket.rooms import DASHBOARD_ROOM, POS_TERMINALS_ROOM, CUSTOMER_DISPLAYS_ROOM


def emit_new_sale(sale):
    socketio.emit("sale:created", sale.to_dict(), room=DASHBOARD_ROOM)
    socketio.emit("sale:created", sale.to_dict(), room=POS_TERMINALS_ROOM)


def emit_notification(notification):
    payload = {
        "id": notification.id,
        "type": notification.type,
        "title": notification.title,
        "message": notification.message,
        "severity": notification.severity,
    }
    socketio.emit("notification:new", payload, room=DASHBOARD_ROOM)


def emit_customer_display_update(sale):
    socketio.emit("customer_display:update", sale.to_dict(), room=CUSTOMER_DISPLAYS_ROOM)


def emit_cash_drawer_open(device):
    socketio.emit("hardware:cash_drawer_open", {"device_id": device.id}, room=POS_TERMINALS_ROOM)


def emit_dashboard_refresh(summary):
    socketio.emit("dashboard:refresh", summary, room=DASHBOARD_ROOM)


def emit_print_job(printer, content, job_type="receipt"):
    """Sent to POS terminal agents; the local agent with driver access performs the actual print."""
    socketio.emit("print:job", {
        "printer_id": printer.id,
        "printer_identifier": printer.identifier,
        "connection_type": printer.connection_type,
        "job_type": job_type,
        "content": content,
    }, room=POS_TERMINALS_ROOM)


def emit_checkout_update(sale_or_dict):
    """Live cart update pushed to the customer display during an active checkout."""
    payload = sale_or_dict.to_dict() if hasattr(sale_or_dict, "to_dict") else sale_or_dict
    socketio.emit("checkout:update", payload, room=CUSTOMER_DISPLAYS_ROOM)


def emit_customer_payment_selected(payload):
    """Sent to the cashier's POS terminal when the customer picks a payment method."""
    socketio.emit("customer:payment_selected", payload, room=POS_TERMINALS_ROOM)


def emit_payment_confirmed(sale):
    socketio.emit("payment:confirmed", sale.to_dict(), room=CUSTOMER_DISPLAYS_ROOM)
    socketio.emit("payment:confirmed", sale.to_dict(), room=POS_TERMINALS_ROOM)


def emit_activity(audit_entry):
    """Live operational feed for the dashboard: every audited action, as it happens."""
    socketio.emit("activity:new", {
        "id": audit_entry.id,
        "action": audit_entry.action,
        "entity_type": audit_entry.entity_type,
        "entity_id": audit_entry.entity_id,
        "user_id": audit_entry.user_id,
        "user_name": audit_entry.user.full_name if audit_entry.user else "System",
        "created_at": audit_entry.created_at.isoformat() if audit_entry.created_at else None,
    }, room=DASHBOARD_ROOM)

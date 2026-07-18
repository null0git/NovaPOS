"""
Connection lifecycle handlers for Socket.IO.

Clients join a room based on their declared role so broadcasts only reach
relevant consumers (e.g. a customer display doesn't need audit-log events).
"""
from flask_socketio import join_room, leave_room, emit

from app.extensions import socketio
from app.websocket.rooms import ALL_ROOMS, DASHBOARD_ROOM, POS_TERMINALS_ROOM, CUSTOMER_DISPLAYS_ROOM, device_room


@socketio.on("connect")
def handle_connect():
    emit("connected", {"message": "Connected to NovaPOS realtime server."})


@socketio.on("disconnect")
def handle_disconnect():
    pass


@socketio.on("join")
def handle_join(data):
    """
    data: { "room": "dashboard" | "pos_terminals" | "customer_displays", "device_id": optional }
    """
    room = data.get("room")
    if room in ALL_ROOMS:
        join_room(room)
        emit("joined", {"room": room})

    device_id = data.get("device_id")
    if device_id:
        join_room(device_room(device_id))


@socketio.on("leave")
def handle_leave(data):
    room = data.get("room")
    if room in ALL_ROOMS:
        leave_room(room)
        emit("left", {"room": room})

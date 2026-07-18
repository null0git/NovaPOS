"""Wires the Socket.IO server into the Flask app and imports the handlers."""


def init_socketio(app):
    from app.extensions import socketio
    socketio.init_app(app)
    # Import registers the @socketio.on(...) handlers as a side effect.
    from app.websocket import handlers  # noqa: F401
    return socketio

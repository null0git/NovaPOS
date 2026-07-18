"""
Application entrypoint.

Uses socketio.run() instead of app.run() so WebSocket connections
(real-time dashboard/customer-display updates) work over the same server.
For production, run behind gunicorn with the eventlet worker instead, e.g.:

    gunicorn --worker-class eventlet -w 1 -b 0.0.0.0:5000 "run:app"
"""
import os

from app import create_app
from app.extensions import socketio

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = app.config.get("DEBUG", False)
    socketio.run(app, host="0.0.0.0", port=port, debug=debug, use_reloader=debug, allow_unsafe_werkzeug=True)

"""
Application factory.

Everything the app needs (extensions, error handlers, middleware, blueprints,
WebSocket server, background scheduler) is wired up here so `create_app()`
returns a fully configured Flask app, and `run.py` just calls it.
"""
import os

from flask import Flask

from app.config import get_config
from app.extensions import db, migrate, jwt, smorest_api


def create_app(config_object=None):
    app = Flask(__name__)
    app.config.from_object(config_object or get_config())

    _ensure_directories(app)
    _init_extensions(app)
    _register_middleware(app)
    _register_error_handlers(app)
    _register_api(app)
    _init_websocket(app)
    _init_scheduler(app)

    from app.cli import register_cli
    register_cli(app)

    return app


def _ensure_directories(app):
    for key in ("UPLOAD_FOLDER", "BACKUP_FOLDER", "LOG_FOLDER"):
        os.makedirs(app.config[key], exist_ok=True)
    for sub in ("products", "receipts", "exports"):
        os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], sub), exist_ok=True)


def _init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    smorest_api.init_app(app)

    # Import security callbacks (user loader, claims loader) as a side effect.
    from app.core.security import jwt as jwt_helpers  # noqa: F401


def _register_middleware(app):
    from app.core.middleware.cors import register_cors
    from app.core.middleware.request_logger import register_request_logging

    register_cors(app)
    register_request_logging(app)


def _register_error_handlers(app):
    from app.core.middleware.error_handler import register_error_handlers
    register_error_handlers(app)


def _register_api(app):
    from app.docs.swagger import register_api_docs
    register_api_docs(app, smorest_api)


def _init_websocket(app):
    from app.websocket.socket_server import init_socketio
    init_socketio(app)


def _init_scheduler(app):
    # Skip the scheduler during tests / CLI commands like `flask db migrate`
    # to avoid spawning background threads unexpectedly.
    if app.config.get("TESTING"):
        return
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        from app.tasks.scheduler import init_scheduler
        init_scheduler(app)

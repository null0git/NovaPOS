"""
Central place for extension instances.

Instantiated here (unbound) and initialized in the application factory
(app/__init__.py) via .init_app(app). This avoids circular imports since
models/services/routes can `from app.extensions import db` freely.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_smorest import Api
from flask_socketio import SocketIO
from apscheduler.schedulers.background import BackgroundScheduler

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
smorest_api = Api()
socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")
scheduler = BackgroundScheduler()

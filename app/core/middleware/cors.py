"""CORS configuration so every registered frontend origin can reach the API."""
from app.extensions import cors


def register_cors(app):
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )

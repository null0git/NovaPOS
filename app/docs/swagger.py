"""
Swagger / OpenAPI documentation wiring.

flask-smorest builds the OpenAPI spec automatically from each Blueprint's
registered schemas and docstrings. Swagger UI is served at /docs (see
OPENAPI_SWAGGER_UI_PATH in config.py) once the Api instance is initialized
and every blueprint is registered on it.
"""


def register_api_docs(app, api):
    from app.api.v1 import ALL_BLUEPRINTS

    for blp in ALL_BLUEPRINTS:
        api.register_blueprint(blp)

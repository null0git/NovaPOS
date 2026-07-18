"""Centralized error handling so every error returns the standard envelope."""
import logging

from flask import Flask
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from app.core.utils.response import error_response

logger = logging.getLogger("novapos")


class AppError(Exception):
    """Base class for predictable, business-logic-raised errors."""

    def __init__(self, message, status_code=400, error_code=None, errors=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.errors = errors


class NotFoundError(AppError):
    def __init__(self, message="Resource not found", **kwargs):
        super().__init__(message, status_code=404, error_code="NOT_FOUND", **kwargs)


class ConflictError(AppError):
    def __init__(self, message="Conflict with current state", **kwargs):
        super().__init__(message, status_code=409, error_code="CONFLICT", **kwargs)


class ValidationAppError(AppError):
    def __init__(self, message="Validation failed", **kwargs):
        super().__init__(message, status_code=422, error_code="VALIDATION_ERROR", **kwargs)


class AuthError(AppError):
    def __init__(self, message="Authentication failed", **kwargs):
        super().__init__(message, status_code=401, error_code="AUTH_ERROR", **kwargs)


class ForbiddenError(AppError):
    def __init__(self, message="Forbidden", **kwargs):
        super().__init__(message, status_code=403, error_code="FORBIDDEN", **kwargs)


def register_error_handlers(app: Flask):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return error_response(err.message, err.status_code, err.errors, err.error_code)

    @app.errorhandler(ValidationError)
    def handle_marshmallow_error(err):
        return error_response("Validation failed", 422, err.messages, "VALIDATION_ERROR")

    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(err):
        logger.exception("Database error")
        from app.extensions import db
        db.session.rollback()
        return error_response("A database error occurred.", 500, error_code="DB_ERROR")

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        return error_response(err.description or err.name, err.code, error_code="HTTP_ERROR")

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        logger.exception("Unhandled exception")
        return error_response("An unexpected error occurred.", 500, error_code="INTERNAL_ERROR")

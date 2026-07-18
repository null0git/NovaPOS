"""
Standard response envelope used by every endpoint in the API.

Keeping one shape for success/error responses means every frontend
(React, RPi display, mobile) can share one parsing layer.
"""
from flask import jsonify


def success_response(data=None, message="Success", status_code=200, meta=None):
    payload = {
        "success": True,
        "message": message,
        "data": data,
    }
    if meta is not None:
        payload["meta"] = meta
    return jsonify(payload), status_code


def error_response(message="An error occurred", status_code=400, errors=None, error_code=None):
    payload = {
        "success": False,
        "message": message,
        "errors": errors,
        "error_code": error_code,
    }
    return jsonify(payload), status_code

"""Request/response logging middleware, written to logs/app.log."""
import logging
import os
import time
from logging.handlers import RotatingFileHandler

from flask import request, g


def setup_logging(app):
    os.makedirs(app.config["LOG_FOLDER"], exist_ok=True)
    log_path = os.path.join(app.config["LOG_FOLDER"], "app.log")

    handler = RotatingFileHandler(log_path, maxBytes=5_000_000, backupCount=5)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s"
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger("novapos")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    if app.config.get("DEBUG"):
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        logger.addHandler(console)

    return logger


def register_request_logging(app):
    logger = setup_logging(app)

    @app.before_request
    def start_timer():
        g._request_start_time = time.time()

    @app.after_request
    def log_request(response):
        duration_ms = (time.time() - g.get("_request_start_time", time.time())) * 1000
        logger.info(
            f'{request.method} {request.path} -> {response.status_code} ({duration_ms:.1f}ms)'
        )
        return response

    return logger

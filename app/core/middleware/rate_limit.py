"""
Lightweight in-memory rate limiter.

For a single-process deployment (typical small-business POS) this avoids
an extra Redis dependency. For multi-worker/production deployments, swap
the `_buckets` dict for a Redis-backed counter without changing the
decorator's call sites.
"""
import time
from collections import defaultdict
from functools import wraps

from flask import request

from app.core.utils.response import error_response

_buckets = defaultdict(list)


def _parse_limit(limit_str):
    # e.g. "5 per minute", "200 per hour"
    count, _, period = limit_str.split(" ")
    count = int(count)
    seconds = {"second": 1, "minute": 60, "hour": 3600, "day": 86400}[period.rstrip("s")]
    return count, seconds


def rate_limit(limit_str="60 per minute"):
    max_count, window_seconds = _parse_limit(limit_str)

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = f"{request.remote_addr}:{request.endpoint}"
            now = time.time()
            bucket = _buckets[key]
            _buckets[key] = [t for t in bucket if now - t < window_seconds]
            if len(_buckets[key]) >= max_count:
                return error_response("Too many requests. Please slow down.", 429, error_code="RATE_LIMITED")
            _buckets[key].append(now)
            return fn(*args, **kwargs)

        return wrapper

    return decorator

"""Datetime helpers used across services/reports."""
from datetime import datetime, timezone, timedelta


def utcnow():
    return datetime.now(timezone.utc)


def to_iso(dt):
    if dt is None:
        return None
    return dt.isoformat()


def start_of_day(dt=None):
    dt = dt or utcnow()
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(dt=None):
    dt = dt or utcnow()
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def humanize_timedelta(dt):
    """Turn a past datetime into a human string: '2 hours ago', '1 month and 2 days ago', etc."""
    if dt is None:
        return None
    now = utcnow()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=now.tzinfo)
    delta = now - dt
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = hours // 24
    if days < 7:
        return f"{days} day{'s' if days != 1 else ''} ago"
    if days < 30:
        weeks = days // 7
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    if days < 365:
        months = days // 30
        remaining_days = days % 30
        if remaining_days == 0:
            return f"{months} month{'s' if months != 1 else ''} ago"
        return (f"{months} month{'s' if months != 1 else ''} and "
                f"{remaining_days} day{'s' if remaining_days != 1 else ''} ago")
    years = days // 365
    return f"{years} year{'s' if years != 1 else ''} ago"


def date_range_from_period(period: str):
    """Return (start, end) datetimes for 'today' | 'week' | 'month' | 'year'."""
    now = utcnow()
    if period == "today":
        return start_of_day(now), end_of_day(now)
    if period == "week":
        start = start_of_day(now) - timedelta(days=now.weekday())
        return start, end_of_day(now)
    if period == "month":
        start = start_of_day(now).replace(day=1)
        return start, end_of_day(now)
    if period == "year":
        start = start_of_day(now).replace(month=1, day=1)
        return start, end_of_day(now)
    return start_of_day(now), end_of_day(now)

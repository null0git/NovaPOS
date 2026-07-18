"""Common query filtering helpers (search, sort, date range)."""
from flask import request


def apply_search(query, model, fields, param="search"):
    term = request.args.get(param)
    if not term:
        return query
    like = f"%{term}%"
    conditions = [getattr(model, f).ilike(like) for f in fields if hasattr(model, f)]
    if not conditions:
        return query
    from sqlalchemy import or_
    return query.filter(or_(*conditions))


def apply_sort(query, model, default_field="id", default_dir="desc"):
    sort_field = request.args.get("sort_by", default_field)
    sort_dir = request.args.get("sort_dir", default_dir)
    column = getattr(model, sort_field, None)
    if column is None:
        column = getattr(model, default_field)
    return query.order_by(column.desc() if sort_dir == "desc" else column.asc())

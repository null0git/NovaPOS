"""Pagination helpers shared by all list endpoints."""
from flask import request


def get_pagination_params():
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except (TypeError, ValueError):
        page = 1
    try:
        per_page = int(request.args.get("per_page", 20))
    except (TypeError, ValueError):
        per_page = 20
    per_page = min(max(per_page, 1), 100)
    return page, per_page


def paginate_query(query, page=None, per_page=None):
    """Paginate a SQLAlchemy query and return (items, meta_dict)."""
    if page is None or per_page is None:
        page, per_page = get_pagination_params()
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    meta = {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total_items": pagination.total,
        "total_pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
    }
    return pagination.items, meta

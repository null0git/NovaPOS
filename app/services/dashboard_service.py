"""
Business logic for the professional dashboard: sales, inventory, payments,
staff performance, hardware status, recent activity, and plain-language
business insights for non-technical store owners.
"""
from collections import Counter
from decimal import Decimal

from sqlalchemy import func

from app.core.utils.datetime_utils import date_range_from_period, utcnow
from app.extensions import db
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.payment import Payment
from app.models.product import Product
from app.models.user import User
from app.repositories.sales_repository import SalesRepository
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.audit_repository import AuditRepository
from app.services.report_service import ReportService
from app.services.system_health_service import SystemHealthService


class DashboardService:
    def __init__(self):
        self.sales_repo = SalesRepository()
        self.inventory_repo = InventoryRepository()
        self.audit_repo = AuditRepository()
        self.report_service = ReportService()
        self.health_service = SystemHealthService()

    def summary(self):
        return {
            "sales": self._sales_section(),
            "inventory": self._inventory_section(),
            "payments": self._payments_section(),
            "staff": self._staff_section(),
            "hardware": self._hardware_section(),
            "recent_activity": self._recent_activity(),
            "insights": self._business_insights(),
        }

    def _sales_section(self):
        today = self.report_service.sales_report(period="today")
        profit = self.report_service.profit_report(period="today")

        start, end = date_range_from_period("today")
        refunds_total = (
            db.session.query(func.coalesce(func.sum(Sale.total_amount), 0))
            .filter(Sale.status.in_(["refunded", "partially_refunded"]),
                    Sale.created_at >= start, Sale.created_at <= end)
            .scalar()
        )

        return {
            "todays_sales_count": today["total_sales_count"],
            "todays_revenue": today["total_revenue"],
            "estimated_profit": profit["gross_profit"],
            "average_sale_value": today["average_sale_value"],
            "refund_summary": {"total_amount": float(refunds_total or 0)},
        }

    def _inventory_section(self):
        from app.models.inventory import Inventory
        products = Product.query.all()
        active_products = [p for p in products if p.is_active]

        inventory_rows = Inventory.query.all()
        inventory_value = sum(
            Decimal(str(row.product.cost_price)) * row.quantity
            for row in inventory_rows if row.product
        )
        low_stock = [i for i in inventory_rows if i.is_low_stock and i.quantity > 0]
        out_of_stock = [i for i in inventory_rows if i.quantity == 0]

        return {
            "total_products": len(products),
            "active_products": len(active_products),
            "inventory_value": float(inventory_value),
            "low_stock_count": len(low_stock),
            "out_of_stock_count": len(out_of_stock),
        }

    def _payments_section(self):
        start, end = date_range_from_period("today")
        rows = (
            db.session.query(Payment.method, func.coalesce(func.sum(Payment.amount), 0))
            .join(Sale, Payment.sale_id == Sale.id)
            .filter(Sale.created_at >= start, Sale.created_at <= end, Payment.status == "completed")
            .group_by(Payment.method)
            .all()
        )
        return {method: float(total) for method, total in rows}

    def _staff_section(self):
        start, end = date_range_from_period("today")
        active_cashiers = User.query.join(User.role).filter(User.is_active.is_(True)).count()

        rows = (
            db.session.query(User.id, User.full_name, func.count(Sale.id), func.coalesce(func.sum(Sale.total_amount), 0))
            .join(Sale, Sale.cashier_id == User.id)
            .filter(Sale.created_at >= start, Sale.created_at <= end, Sale.status != "voided")
            .group_by(User.id, User.full_name)
            .order_by(func.sum(Sale.total_amount).desc())
            .all()
        )
        return {
            "active_cashiers": active_cashiers,
            "sales_by_cashier": [
                {"user_id": r[0], "name": r[1], "sales_count": r[2], "revenue": float(r[3])} for r in rows
            ],
        }

    def _hardware_section(self):
        return {
            "printers": self.health_service.check_printers(),
            "customer_displays": self.health_service.check_customer_displays(),
        }

    def _recent_activity(self, limit=10):
        recent = self.audit_repo.get_all().order_by(self.audit_repo.model.created_at.desc()).limit(limit).all()
        return [a.to_dict() for a in recent]

    def _business_insights(self):
        insights = []

        today_start, today_end = date_range_from_period("today")
        yesterday_start = today_start - (today_end - today_start) - __import__("datetime").timedelta(seconds=1)
        yesterday_end = today_start - __import__("datetime").timedelta(microseconds=1)

        today_revenue = db.session.query(func.coalesce(func.sum(Sale.total_amount), 0)).filter(
            Sale.created_at >= today_start, Sale.created_at <= today_end, Sale.status != "voided"
        ).scalar()
        yesterday_revenue = db.session.query(func.coalesce(func.sum(Sale.total_amount), 0)).filter(
            Sale.created_at >= yesterday_start, Sale.created_at <= yesterday_end, Sale.status != "voided"
        ).scalar()

        if yesterday_revenue and yesterday_revenue > 0:
            change_pct = ((float(today_revenue) - float(yesterday_revenue)) / float(yesterday_revenue)) * 100
            direction = "increased" if change_pct >= 0 else "decreased"
            insights.append(f"Sales {direction} by {abs(change_pct):.0f}% compared to yesterday.")

        top_products = self.report_service.top_products(period="today", limit=1)
        if top_products:
            insights.append(f"{top_products[0]['product_name']} is today's best-selling product.")

        low_stock_count = self._inventory_section()["low_stock_count"]
        if low_stock_count:
            insights.append(f"{low_stock_count} product{'s' if low_stock_count != 1 else ''} need restocking.")

        peak_hour = self._peak_sales_hour(today_start, today_end)
        if peak_hour is not None:
            insights.append(f"Peak sales time was between {peak_hour}:00 and {peak_hour + 1}:00.")

        return insights

    def _peak_sales_hour(self, start, end):
        sales = Sale.query.filter(Sale.created_at >= start, Sale.created_at <= end,
                                   Sale.status != "voided").all()
        if not sales:
            return None
        hour_counts = Counter(s.created_at.hour for s in sales)
        return hour_counts.most_common(1)[0][0]

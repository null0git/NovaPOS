"""Business logic for aggregated reporting (sales, profit, top products, inventory)."""
from decimal import Decimal

from sqlalchemy import func

from app.core.utils.datetime_utils import date_range_from_period
from app.extensions import db
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.product import Product
from app.repositories.sales_repository import SalesRepository
from app.repositories.inventory_repository import InventoryRepository


class ReportService:
    def __init__(self):
        self.sales_repo = SalesRepository()
        self.inventory_repo = InventoryRepository()

    def _resolve_range(self, period, start_date=None, end_date=None):
        if period == "custom" and start_date and end_date:
            return start_date, end_date
        return date_range_from_period(period)

    def sales_report(self, period="today", start_date=None, end_date=None):
        start, end = self._resolve_range(period, start_date, end_date)
        sales = self.sales_repo.get_between(start, end).filter(Sale.status != "voided")

        count = sales.count()
        totals = sales.with_entities(
            func.coalesce(func.sum(Sale.total_amount), 0),
            func.coalesce(func.sum(Sale.tax_amount), 0),
            func.coalesce(func.sum(Sale.discount_amount), 0),
        ).first()

        revenue, tax, discount = totals
        avg_sale = (revenue / count) if count else 0

        return {
            "period": period,
            "total_sales_count": count,
            "total_revenue": float(revenue),
            "total_tax": float(tax),
            "total_discount": float(discount),
            "average_sale_value": float(avg_sale),
        }

    def profit_report(self, period="today", start_date=None, end_date=None):
        start, end = self._resolve_range(period, start_date, end_date)

        rows = (
            db.session.query(
                SaleItem.quantity, SaleItem.line_total, Product.cost_price
            )
            .join(Sale, SaleItem.sale_id == Sale.id)
            .join(Product, SaleItem.product_id == Product.id)
            .filter(Sale.created_at >= start, Sale.created_at <= end, Sale.status != "voided")
            .all()
        )

        total_revenue = sum(Decimal(str(r.line_total)) for r in rows) if rows else Decimal("0")
        total_cost = sum(Decimal(str(r.cost_price)) * r.quantity for r in rows) if rows else Decimal("0")
        gross_profit = total_revenue - total_cost
        margin = (gross_profit / total_revenue * 100) if total_revenue else Decimal("0")

        return {
            "period": period,
            "total_revenue": float(total_revenue),
            "total_cost": float(total_cost),
            "gross_profit": float(gross_profit),
            "margin_percent": float(margin),
        }

    def top_products(self, period="today", start_date=None, end_date=None, limit=10):
        start, end = self._resolve_range(period, start_date, end_date)

        rows = (
            db.session.query(
                Product.id, Product.name,
                func.sum(SaleItem.quantity).label("quantity_sold"),
                func.sum(SaleItem.line_total).label("revenue"),
            )
            .join(SaleItem, SaleItem.product_id == Product.id)
            .join(Sale, SaleItem.sale_id == Sale.id)
            .filter(Sale.created_at >= start, Sale.created_at <= end, Sale.status != "voided")
            .group_by(Product.id, Product.name)
            .order_by(func.sum(SaleItem.quantity).desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "product_id": r.id,
                "product_name": r.name,
                "quantity_sold": int(r.quantity_sold),
                "revenue": float(r.revenue),
            }
            for r in rows
        ]

    def inventory_report(self):
        inventories = self.inventory_repo.get_all().all()
        return {
            "total_products": len(inventories),
            "low_stock_count": sum(1 for i in inventories if i.is_low_stock),
            "total_units_on_hand": sum(i.quantity for i in inventories),
            "low_stock_items": [i.to_dict() for i in inventories if i.is_low_stock],
        }

    def daily_closing_report(self, date=None):
        """Professional end-of-day summary: sales, payments, refunds, discounts,
        cashier performance, inventory summary, and hardware status."""
        from app.core.utils.datetime_utils import start_of_day, end_of_day, utcnow
        from app.models.sale import Sale
        from app.models.payment import Payment
        from app.models.refund import Refund
        from app.models.discount_log import DiscountLog
        from app.services.dashboard_service import DashboardService

        reference = date or utcnow()
        start, end = start_of_day(reference), end_of_day(reference)

        sales_report = self.sales_report(period="custom", start_date=start, end_date=end)
        profit_report = self.profit_report(period="custom", start_date=start, end_date=end)

        payments_by_method = dict(
            db.session.query(Payment.method, func.coalesce(func.sum(Payment.amount), 0))
            .join(Sale, Payment.sale_id == Sale.id)
            .filter(Sale.created_at >= start, Sale.created_at <= end, Payment.status == "completed")
            .group_by(Payment.method).all()
        )
        payments_by_method = {k: float(v) for k, v in payments_by_method.items()}

        refunds_total = db.session.query(func.coalesce(func.sum(Refund.amount), 0)).join(
            Sale, Refund.sale_id == Sale.id
        ).filter(Sale.created_at >= start, Sale.created_at <= end, Refund.status == "completed").scalar()

        discounts_total = db.session.query(func.coalesce(func.sum(DiscountLog.discount_amount), 0)).filter(
            DiscountLog.created_at >= start, DiscountLog.created_at <= end
        ).scalar()

        cashier_rows = (
            db.session.query(Sale.cashier_id, func.count(Sale.id), func.coalesce(func.sum(Sale.total_amount), 0))
            .filter(Sale.created_at >= start, Sale.created_at <= end, Sale.status != "voided")
            .group_by(Sale.cashier_id).all()
        )
        from app.models.user import User
        cashier_performance = []
        for cashier_id, count, total in cashier_rows:
            user = User.query.get(cashier_id)
            cashier_performance.append({
                "cashier_id": cashier_id, "cashier_name": user.full_name if user else "Unknown",
                "sales_count": count, "revenue": float(total),
            })

        return {
            "date": start.date().isoformat(),
            "sales": sales_report,
            "profit": profit_report,
            "payments_by_method": payments_by_method,
            "refunds_total": float(refunds_total or 0),
            "discounts_total": float(discounts_total or 0),
            "cashier_performance": cashier_performance,
            "inventory_summary": self.inventory_report(),
            "hardware_status": DashboardService()._hardware_section(),
        }

    def product_analytics(self, period="month", limit=10):
        """Top-selling, highest-revenue/profit, fastest-growing, slow-moving, most-refunded,
        and products nearing stock depletion — for the advanced analytics dashboard."""
        from app.models.sale import Sale
        from app.models.sale_item import SaleItem
        from app.models.refund import Refund
        from app.models.inventory import Inventory
        start, end = date_range_from_period(period)
        prev_start, prev_end = start - (end - start), start

        def sales_totals(range_start, range_end):
            return (
                db.session.query(
                    Product.id, Product.name,
                    func.sum(SaleItem.quantity).label("qty"),
                    func.sum(SaleItem.line_total).label("revenue"),
                )
                .join(SaleItem, SaleItem.product_id == Product.id)
                .join(Sale, SaleItem.sale_id == Sale.id)
                .filter(Sale.created_at >= range_start, Sale.created_at <= range_end, Sale.status != "voided")
                .group_by(Product.id, Product.name)
                .all()
            )

        current = {r.id: r for r in sales_totals(start, end)}
        previous = {r.id: r for r in sales_totals(prev_start, prev_end)}

        top_selling = sorted(current.values(), key=lambda r: r.qty, reverse=True)[:limit]
        highest_revenue = sorted(current.values(), key=lambda r: r.revenue, reverse=True)[:limit]

        profit_rows = (
            db.session.query(Product.id, Product.name, Product.cost_price,
                              func.sum(SaleItem.quantity).label("qty"), func.sum(SaleItem.line_total).label("rev"))
            .join(SaleItem, SaleItem.product_id == Product.id)
            .join(Sale, SaleItem.sale_id == Sale.id)
            .filter(Sale.created_at >= start, Sale.created_at <= end, Sale.status != "voided")
            .group_by(Product.id, Product.name, Product.cost_price).all()
        )
        highest_profit = sorted(
            profit_rows, key=lambda r: float(r.rev) - float(r.cost_price) * r.qty, reverse=True
        )[:limit]

        fastest_growing = []
        for pid, row in current.items():
            prev_qty = previous[pid].qty if pid in previous else 0
            if prev_qty > 0:
                growth = ((row.qty - prev_qty) / prev_qty) * 100
            elif row.qty > 0:
                growth = 100.0
            else:
                growth = 0.0
            fastest_growing.append({"product_id": pid, "product_name": row.name, "growth_percent": growth})
        fastest_growing = sorted(fastest_growing, key=lambda r: r["growth_percent"], reverse=True)[:limit]

        all_active_products = Product.query.filter_by(is_active=True).all()
        slow_moving = [
            {"product_id": p.id, "product_name": p.name, "quantity_sold": current.get(p.id).qty if p.id in current else 0}
            for p in all_active_products if p.id not in current
        ][:limit]

        most_refunded_rows = (
            db.session.query(Product.id, Product.name, func.sum(Refund.quantity).label("qty"))
            .join(SaleItem, Refund.sale_item_id == SaleItem.id)
            .join(Product, SaleItem.product_id == Product.id)
            .filter(Refund.created_at >= start, Refund.created_at <= end, Refund.status == "completed")
            .group_by(Product.id, Product.name)
            .order_by(func.sum(Refund.quantity).desc())
            .limit(limit).all()
        )

        nearing_depletion = [
            i.to_dict() for i in Inventory.query.filter(Inventory.quantity > 0,
                                                          Inventory.quantity <= Inventory.low_stock_threshold).all()
        ][:limit]

        return {
            "period": period,
            "top_selling": [{"product_id": r.id, "product_name": r.name, "quantity_sold": int(r.qty)} for r in top_selling],
            "highest_revenue": [{"product_id": r.id, "product_name": r.name, "revenue": float(r.revenue)} for r in highest_revenue],
            "highest_profit": [
                {"product_id": r.id, "product_name": r.name,
                 "profit": float(r.rev) - float(r.cost_price) * r.qty} for r in highest_profit
            ],
            "fastest_growing": fastest_growing,
            "slow_moving": slow_moving,
            "most_refunded": [{"product_id": r.id, "product_name": r.name, "quantity_refunded": int(r.qty)} for r in most_refunded_rows],
            "nearing_depletion": nearing_depletion,
        }

    def business_calendar(self, year, month):
        """Per-day aggregates for a month, for the interactive business calendar."""
        import calendar as cal_module
        from datetime import datetime, timezone
        from app.models.sale import Sale
        from app.models.refund import Refund
        from app.models.customer import Customer
        from app.models.inventory_history import InventoryHistory
        from app.models.backup import Backup

        days_in_month = cal_module.monthrange(year, month)[1]
        days = []
        for day in range(1, days_in_month + 1):
            start = datetime(year, month, day, 0, 0, 0, tzinfo=timezone.utc)
            end = datetime(year, month, day, 23, 59, 59, 999999, tzinfo=timezone.utc)

            sales_count = Sale.query.filter(Sale.created_at >= start, Sale.created_at <= end,
                                             Sale.status != "voided").count()
            revenue = db.session.query(func.coalesce(func.sum(Sale.total_amount), 0)).filter(
                Sale.created_at >= start, Sale.created_at <= end, Sale.status != "voided"
            ).scalar()
            refunds_count = Refund.query.filter(Refund.created_at >= start, Refund.created_at <= end).count()
            inventory_events = InventoryHistory.query.filter(
                InventoryHistory.created_at >= start, InventoryHistory.created_at <= end
            ).count()
            new_customers = Customer.query.filter(Customer.created_at >= start, Customer.created_at <= end).count()
            backups = Backup.query.filter(Backup.created_at >= start, Backup.created_at <= end).count()

            days.append({
                "date": start.date().isoformat(),
                "sales_count": sales_count,
                "revenue": float(revenue or 0),
                "refunds_count": refunds_count,
                "inventory_events": inventory_events,
                "new_customers": new_customers,
                "backups": backups,
            })

        return {"year": year, "month": month, "days": days}

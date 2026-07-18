"""End-of-day job that stores a daily sales report as a notification/log entry."""
import logging

logger = logging.getLogger("novapos")


def daily_report_snapshot_job(app):
    with app.app_context():
        from app.services.report_service import ReportService
        from app.services.notification_service import NotificationService

        report = ReportService().sales_report(period="today")
        NotificationService().create(
            type_="daily_report",
            title="Daily sales summary",
            message=(
                f"{report['total_sales_count']} sales, "
                f"revenue {report['total_revenue']:.2f}."
            ),
            severity="info",
            meta=report,
        )
        logger.info(f"Daily report snapshot generated: {report}")

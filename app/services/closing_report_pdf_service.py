"""PDF generation for the daily store-closing report."""
import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


class ClosingReportPDFService:
    def generate_pdf(self, report, business_name="NovaPOS Store"):
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        width, height = A4
        y = height - 20 * mm

        def line(text, size=10, bold=False, gap=6 * mm):
            nonlocal y
            c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
            c.drawString(20 * mm, y, text)
            y -= gap

        line(f"{business_name} — Daily Closing Report", size=14, bold=True, gap=10 * mm)
        line(f"Date: {report['date']}", size=10)
        line("")

        sales = report["sales"]
        line("Sales Summary", size=12, bold=True)
        line(f"Transactions: {sales['total_sales_count']}")
        line(f"Revenue: {sales['total_revenue']:.2f}")
        line(f"Tax collected: {sales['total_tax']:.2f}")
        line(f"Discounts given: {sales['total_discount']:.2f}")
        line(f"Average sale value: {sales['average_sale_value']:.2f}")
        line("")

        profit = report["profit"]
        line("Profit", size=12, bold=True)
        line(f"Estimated gross profit: {profit['gross_profit']:.2f} (margin {profit['margin_percent']:.1f}%)")
        line("")

        line("Payments by method", size=12, bold=True)
        for method, amount in report["payments_by_method"].items():
            line(f"  {method}: {amount:.2f}")
        line("")

        line("Refunds & Discounts", size=12, bold=True)
        line(f"Total refunded: {report['refunds_total']:.2f}")
        line(f"Total discounted: {report['discounts_total']:.2f}")
        line("")

        line("Cashier Performance", size=12, bold=True)
        for c_perf in report["cashier_performance"]:
            line(f"  {c_perf['cashier_name']}: {c_perf['sales_count']} sales, {c_perf['revenue']:.2f} revenue")
        line("")

        inv = report["inventory_summary"]
        line("Inventory Summary", size=12, bold=True)
        line(f"Total products: {inv['total_products']}, Low stock: {inv['low_stock_count']}")
        line("")

        hw = report["hardware_status"]
        line("Hardware Status", size=12, bold=True)
        line(f"Printers online: {hw['printers']['online']}/{hw['printers']['total']}")
        line(f"Customer displays online: {hw['customer_displays']['online']}/{hw['customer_displays']['total']}")

        c.save()
        buf.seek(0)
        return buf.read()

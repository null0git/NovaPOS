"""PDF generation for receipts (download / reprint) — a receipt-sized PDF, not a full page."""
import io

from reportlab.lib.pagesizes import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.core.utils.datetime_utils import to_iso
from app.core.utils.qr_code import generate_qr_bytes

WIDTH_BY_MM = {58: 58 * mm, 80: 80 * mm}


class ReceiptPDFService:
    def generate_pdf(self, sale, business_name="NovaPOS Store", footer_text="Thank you for shopping with us!",
                      refund_policy=None, paper_width_mm=80, logo_path=None):
        receipt_width = WIDTH_BY_MM.get(paper_width_mm, 80 * mm)
        line_height = 4.2 * mm
        lines_estimate = 16 + len(sale.items) * 3 + len(sale.payments) * 2 + (3 if refund_policy else 0)
        height = max(lines_estimate * line_height + 40 * mm, 110 * mm)  # extra room for the QR code

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=(receipt_width, height))
        y = height - 8 * mm
        x_center = receipt_width / 2

        def line(text, font="Helvetica", size=8, center=True, bold=False):
            nonlocal y
            c.setFont("Helvetica-Bold" if bold else font, size)
            if center:
                c.drawCentredString(x_center, y, text)
            else:
                c.drawString(4 * mm, y, text)
            y -= line_height

        if logo_path:
            try:
                logo_size = 10 * mm
                c.drawImage(ImageReader(logo_path), x_center - logo_size / 2, y - logo_size,
                            width=logo_size, height=logo_size, mask="auto", preserveAspectRatio=True)
                y -= logo_size + 2 * mm
            except Exception:
                pass

        line(business_name, bold=True, size=11)
        line("=" * 32, size=7)
        line(f"Receipt #: {sale.receipt_number}", center=False)
        line(f"Date: {to_iso(sale.created_at)}", center=False)
        if sale.cashier:
            line(f"Cashier: {sale.cashier.full_name}", center=False)
        if sale.customer:
            line(f"Customer: {sale.customer.name}", center=False)
        line("-" * 32, size=7)

        for item in sale.items:
            name = item.product.name if item.product else "Item"
            if item.variant:
                name = f"{name} ({item.variant.name})"
            line(f"{name[:32]}", center=False, size=8)
            line(f"  {item.quantity} x {float(item.unit_price):.2f} = {float(item.line_total):.2f}",
                 center=False, size=8)
            if item.discount_amount and float(item.discount_amount) > 0:
                line(f"  Discount: -{float(item.discount_amount):.2f}", center=False, size=7)

        line("-" * 32, size=7)
        line(f"Subtotal: {float(sale.subtotal):.2f}", center=False)
        line(f"Tax: {float(sale.tax_amount):.2f}", center=False)
        if float(sale.discount_amount) > 0:
            line(f"Discount: -{float(sale.discount_amount):.2f}", center=False)
        line(f"TOTAL: {float(sale.total_amount):.2f}", center=False, bold=True, size=10)

        if sale.payments:
            line("-" * 32, size=7)
            for payment in sale.payments:
                line(f"Paid ({payment.method}): {float(payment.amount):.2f}", center=False)
                if payment.amount_tendered:
                    line(f"Tendered: {float(payment.amount_tendered):.2f}", center=False, size=7)
                if payment.change_due:
                    line(f"Change: {float(payment.change_due):.2f}", center=False, size=7)

        line("=" * 32, size=7)

        if sale.verification_code:
            qr_bytes = generate_qr_bytes(f"verify:{sale.verification_code}")
            qr_size = 18 * mm
            c.drawImage(ImageReader(io.BytesIO(qr_bytes)), x_center - qr_size / 2, y - qr_size,
                        width=qr_size, height=qr_size, mask="auto")
            y -= qr_size + 2 * mm
            line(f"Verify: {sale.verification_code}", size=7)

        line(footer_text, size=8)
        if refund_policy:
            line("-" * 32, size=6)
            for chunk in [refund_policy[i:i + 34] for i in range(0, len(refund_policy), 34)]:
                line(chunk, size=6)

        c.save()
        buf.seek(0)
        return buf.read()

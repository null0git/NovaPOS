"""Plain-text receipt formatting (for thermal printers / PDF export)."""
from app.core.utils.datetime_utils import to_iso

# Standard thermal printer character widths at typical font settings.
WIDTH_BY_MM = {58: 32, 80: 42}


def format_receipt_text(sale, business_name="NovaPOS Store", paper_width_mm=80,
                         refund_policy=None, footer_text="Thank you for shopping with us!"):
    """Build a monospace receipt string from a Sale object, sized for a 58mm or 80mm printer."""
    width = WIDTH_BY_MM.get(paper_width_mm, 42)
    lines = []

    lines.append(business_name.center(width))
    lines.append("=" * width)
    lines.append(f"Receipt #: {sale.receipt_number}")
    lines.append(f"Date: {to_iso(sale.created_at)}")
    if sale.cashier:
        lines.append(f"Cashier: {sale.cashier.full_name}")
    if sale.customer:
        lines.append(f"Customer: {sale.customer.name}")
    lines.append("-" * width)

    for item in sale.items:
        name = item.product.name if item.product else "Item"
        if item.variant:
            name = f"{name} ({item.variant.name})"
        if item.unit:
            name = f"{name} [{item.unit.unit_name}]"
        line1 = f"{name[:width]}"
        qty_price = f"{item.quantity} x {float(item.unit_price):.2f}"
        total = f"{float(item.line_total):.2f}"
        lines.append(line1)
        pad = width - len(qty_price) - len(total)
        lines.append(f"  {qty_price}{' ' * max(pad, 1)}{total}")
        if item.discount_amount and float(item.discount_amount) > 0:
            lines.append(f"  Discount: -{float(item.discount_amount):.2f}")

    lines.append("-" * width)

    def money_line(label, value):
        value_str = f"{value:.2f}"
        pad = width - len(label) - len(value_str)
        return f"{label}{' ' * max(pad, 1)}{value_str}"

    lines.append(money_line("Subtotal", float(sale.subtotal)))
    lines.append(money_line("Tax", float(sale.tax_amount)))
    if float(sale.discount_amount) > 0:
        lines.append(money_line("Discount", -float(sale.discount_amount)))
    lines.append(money_line("TOTAL", float(sale.total_amount)))

    if sale.payments:
        lines.append("-" * width)
        for payment in sale.payments:
            lines.append(money_line(f"Paid ({payment.method})", float(payment.amount)))
            if payment.amount_tendered:
                lines.append(money_line("Tendered", float(payment.amount_tendered)))
            if payment.change_due:
                lines.append(money_line("Change", float(payment.change_due)))

    lines.append("=" * width)
    if sale.verification_code:
        lines.append(f"Verify: {sale.verification_code}".center(width))
    lines.append(footer_text.center(width) if len(footer_text) <= width else footer_text)
    if refund_policy:
        lines.append("-" * width)
        lines.append(refund_policy)

    return "\n".join(lines)

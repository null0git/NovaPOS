"""
Generates printable PDF sheets of Code128 barcode labels for a batch of
internally-generated barcodes (see BarcodeService.bulk_generate). Supports
a few common label sizes and optional store branding on each label.
"""
import io
import os

import barcode as barcode_lib
from barcode.writer import ImageWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

LABEL_SIZES = {
    "small": (38 * mm, 20 * mm),    # common small jewelry/retail label
    "medium": (50 * mm, 30 * mm),
    "large": (70 * mm, 40 * mm),
}


class LabelService:
    def _barcode_image(self, code):
        code_class = barcode_lib.get_barcode_class("code128")
        instance = code_class(code, writer=ImageWriter())
        buf = io.BytesIO()
        instance.write(buf, options={"write_text": False, "module_height": 8.0, "quiet_zone": 1})
        buf.seek(0)
        return ImageReader(buf)

    def generate_label_sheet_pdf(self, entries, product, label_size="medium", store_name=None,
                                  logo_path=None, show_price=True, show_sku=True):
        """
        entries: list of GeneratedBarcode (or objects with `.code`).
        Returns raw PDF bytes for a sheet of labels, tiled across A4 pages.
        """
        label_w, label_h = LABEL_SIZES.get(label_size, LABEL_SIZES["medium"])
        page_w, page_h = A4
        margin = 5 * mm

        cols = max(int((page_w - 2 * margin) // label_w), 1)
        rows = max(int((page_h - 2 * margin) // label_h), 1)
        per_page = cols * rows

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)

        logo_reader = None
        if logo_path and os.path.exists(logo_path):
            try:
                logo_reader = ImageReader(logo_path)
            except Exception:
                logo_reader = None

        for idx, entry in enumerate(entries):
            pos_in_page = idx % per_page
            if idx > 0 and pos_in_page == 0:
                c.showPage()

            col = pos_in_page % cols
            row = pos_in_page // cols
            x = margin + col * label_w
            y = page_h - margin - (row + 1) * label_h

            self._draw_label(c, x, y, label_w, label_h, entry.code, product, store_name,
                              logo_reader, show_price, show_sku)

        c.save()
        buf.seek(0)
        return buf.read()

    def _draw_label(self, c, x, y, w, h, code, product, store_name, logo_reader, show_price, show_sku):
        c.rect(x, y, w, h)
        text_y = y + h - 4 * mm
        cursor_x = x + 2 * mm

        if logo_reader:
            logo_size = 4 * mm
            c.drawImage(logo_reader, cursor_x, text_y - logo_size + 1 * mm,
                        width=logo_size, height=logo_size, mask="auto")
            cursor_x += logo_size + 1 * mm

        if store_name:
            c.setFont("Helvetica-Bold", 6)
            c.drawString(cursor_x, text_y, store_name[:22])

        c.setFont("Helvetica", 6)
        c.drawString(x + 2 * mm, y + h - 8 * mm, (product.name or "")[:26])

        if show_sku:
            c.setFont("Helvetica", 5)
            c.drawString(x + 2 * mm, y + h - 11 * mm, f"SKU: {product.sku}")

        barcode_img = self._barcode_image(code)
        barcode_h = 6 * mm
        barcode_w = w - 4 * mm
        c.drawImage(barcode_img, x + 2 * mm, y + 3 * mm, width=barcode_w, height=barcode_h, mask="auto")

        c.setFont("Helvetica", 5)
        c.drawCentredString(x + w / 2, y + 1 * mm, code)

        if show_price:
            c.setFont("Helvetica-Bold", 7)
            c.drawRightString(x + w - 2 * mm, y + h - 8 * mm, f"{float(product.price):.2f}")

"""QR code generation, e.g. for receipts / customer display payment links."""
import io
import qrcode


def generate_qr_bytes(data: str) -> bytes:
    img = qrcode.make(data)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()

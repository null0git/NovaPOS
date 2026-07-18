"""Barcode generation for products (CODE128)."""
import io
import os
import barcode
from barcode.writer import ImageWriter


def generate_barcode_image(code: str, folder: str) -> str:
    """Generate a CODE128 barcode PNG for `code`, saved under `folder`.

    Returns the filename (not full path).
    """
    os.makedirs(folder, exist_ok=True)
    code_class = barcode.get_barcode_class("code128")
    instance = code_class(code, writer=ImageWriter())
    filename = f"{code}"
    full_path_no_ext = os.path.join(folder, filename)
    saved_path = instance.save(full_path_no_ext)
    return os.path.basename(saved_path)


def generate_barcode_bytes(code: str) -> bytes:
    """Generate a CODE128 barcode PNG in-memory, returning raw bytes."""
    code_class = barcode.get_barcode_class("code128")
    instance = code_class(code, writer=ImageWriter())
    buffer = io.BytesIO()
    instance.write(buffer)
    return buffer.getvalue()

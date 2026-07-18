"""File handling helpers for uploads (product images, exports, receipts)."""
import os
import uuid
from werkzeug.utils import secure_filename

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename, allowed_extensions=ALLOWED_IMAGE_EXTENSIONS):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def generate_unique_filename(original_filename):
    ext = original_filename.rsplit(".", 1)[1].lower() if "." in original_filename else ""
    safe_name = secure_filename(original_filename.rsplit(".", 1)[0])[:40]
    unique = uuid.uuid4().hex[:12]
    return f"{safe_name}_{unique}.{ext}" if ext else f"{safe_name}_{unique}"


def save_upload(file_storage, folder):
    """Save a werkzeug FileStorage to `folder`, returning the stored filename."""
    os.makedirs(folder, exist_ok=True)
    filename = generate_unique_filename(file_storage.filename)
    path = os.path.join(folder, filename)
    file_storage.save(path)
    return filename, path


def delete_file(path):
    if path and os.path.exists(path):
        os.remove(path)
        return True
    return False

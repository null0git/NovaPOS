from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class ReceiptTemplate(db.Model, TimestampMixin, SerializerMixin):
    """
    Stores a receipt layout designed in the (frontend) drag-and-drop designer.
    `layout` is an opaque JSON structure (element list with type/position/
    binding, e.g. logo/store_name/items_table/qr_code/footer_text) that the
    frontend renders in the designer and the backend uses to decide what to
    include when generating the actual PDF/thermal receipt.
    """
    __tablename__ = "receipt_templates"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    paper_width_mm = db.Column(db.Integer, nullable=False, default=80)  # 58 or 80
    layout = db.Column(db.JSON, nullable=False, default=dict)
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<ReceiptTemplate {self.name}>"


class LabelTemplate(db.Model, TimestampMixin, SerializerMixin):
    """Stores a barcode label layout designed in the (frontend) drag-and-drop designer."""
    __tablename__ = "label_templates"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    label_size = db.Column(db.String(20), nullable=False, default="medium")  # small, medium, large
    layout = db.Column(db.JSON, nullable=False, default=dict)
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<LabelTemplate {self.name}>"

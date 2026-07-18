from app.extensions import db
from app.models._base import TimestampMixin, SerializerMixin


class GeneratedBarcode(db.Model, TimestampMixin, SerializerMixin):
    """
    One row per individually-generated internal barcode (e.g. 100 unique
    barcodes for a batch of "5L Cooking Oil"), so labels can be reprinted
    later without regenerating new codes.
    """
    __tablename__ = "generated_barcodes"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    batch_label = db.Column(db.String(100))  # e.g. "2026-07-08 batch of 100"
    printed = db.Column(db.Boolean, default=False, nullable=False)
    printed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    product = db.relationship("Product")

    def __repr__(self):
        return f"<GeneratedBarcode {self.code} product={self.product_id}>"

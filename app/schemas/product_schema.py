from marshmallow import Schema, fields, validate

from app.core.utils.validators import validate_sku


class ProductCreateSchema(Schema):
    sku = fields.String(required=True, validate=validate_sku)
    barcode = fields.String(required=False, allow_none=True)
    name = fields.String(required=True, validate=validate.Length(min=1, max=150))
    description = fields.String(required=False, allow_none=True)
    price = fields.Decimal(required=True, places=2, as_string=False, validate=validate.Range(min=0))
    cost_price = fields.Decimal(required=False, places=2, as_string=False, validate=validate.Range(min=0))
    tax_rate = fields.Decimal(required=False, places=2, as_string=False, validate=validate.Range(min=0, max=100))
    category_id = fields.Integer(required=False, allow_none=True)
    unit = fields.String(required=False)
    initial_stock = fields.Integer(required=False, load_default=0, validate=validate.Range(min=0))
    low_stock_threshold = fields.Integer(required=False, load_default=5, validate=validate.Range(min=0))
    generate_barcode = fields.Boolean(required=False, load_default=False)
    is_tax_exempt = fields.Boolean(required=False, load_default=False)


class ProductUpdateSchema(Schema):
    sku = fields.String(required=False, validate=validate_sku)
    barcode = fields.String(required=False, allow_none=True)
    name = fields.String(required=False, validate=validate.Length(min=1, max=150))
    description = fields.String(required=False, allow_none=True)
    price = fields.Decimal(required=False, places=2, as_string=False, validate=validate.Range(min=0))
    cost_price = fields.Decimal(required=False, places=2, as_string=False, validate=validate.Range(min=0))
    tax_rate = fields.Decimal(required=False, places=2, as_string=False, validate=validate.Range(min=0, max=100))
    category_id = fields.Integer(required=False, allow_none=True)
    unit = fields.String(required=False)
    is_active = fields.Boolean(required=False)
    is_tax_exempt = fields.Boolean(required=False)


class ProductResponseSchema(Schema):
    id = fields.Integer()
    sku = fields.String()
    barcode = fields.String(allow_none=True)
    name = fields.String()
    description = fields.String(allow_none=True)
    price = fields.Float()
    cost_price = fields.Float()
    tax_rate = fields.Float()
    category_id = fields.Integer(allow_none=True)
    category_name = fields.String(allow_none=True)
    current_stock = fields.Integer()
    unit = fields.String()
    is_active = fields.Boolean()
    is_tax_exempt = fields.Boolean()
    image_filename = fields.String(allow_none=True)
    barcode_image_filename = fields.String(allow_none=True)
    created_at = fields.String()
    updated_at = fields.String()

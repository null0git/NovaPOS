from marshmallow import Schema, fields, validate


class VariantCreateSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    sku = fields.String(required=True, validate=validate.Length(min=1, max=50))
    barcode = fields.String(required=False, allow_none=True)
    price = fields.Decimal(required=True, places=2, as_string=False, validate=validate.Range(min=0))
    cost_price = fields.Decimal(required=False, places=2, as_string=False, load_default=0)
    stock_quantity = fields.Integer(required=False, load_default=0, validate=validate.Range(min=0))
    low_stock_threshold = fields.Integer(required=False, load_default=5, validate=validate.Range(min=0))


class VariantUpdateSchema(Schema):
    name = fields.String(required=False)
    sku = fields.String(required=False)
    barcode = fields.String(required=False, allow_none=True)
    price = fields.Decimal(required=False, places=2, as_string=False)
    cost_price = fields.Decimal(required=False, places=2, as_string=False)
    low_stock_threshold = fields.Integer(required=False)
    is_active = fields.Boolean(required=False)


class VariantStockAdjustSchema(Schema):
    quantity_change = fields.Integer(required=True)
    reason = fields.String(required=False, load_default="Adjustment")

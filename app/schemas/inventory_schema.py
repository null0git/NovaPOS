from marshmallow import Schema, fields, validate


class InventoryAdjustSchema(Schema):
    quantity_change = fields.Integer(required=True)
    reason = fields.String(required=True, validate=validate.Length(min=1, max=255))


class InventoryRestockSchema(Schema):
    quantity = fields.Integer(required=True, validate=validate.Range(min=1))
    reason = fields.String(required=False, load_default="Restock")


class InventoryThresholdSchema(Schema):
    low_stock_threshold = fields.Integer(required=False, validate=validate.Range(min=0))
    reorder_quantity = fields.Integer(required=False, validate=validate.Range(min=0))


class InventoryResponseSchema(Schema):
    id = fields.Integer()
    product_id = fields.Integer()
    product_name = fields.String()
    quantity = fields.Integer()
    low_stock_threshold = fields.Integer()
    reorder_quantity = fields.Integer()
    is_low_stock = fields.Boolean()

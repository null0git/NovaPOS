from marshmallow import Schema, fields, validate


class PaymentResponseSchema(Schema):
    id = fields.Integer()
    sale_id = fields.Integer()
    method = fields.String()
    amount = fields.Float()
    amount_tendered = fields.Float(allow_none=True)
    change_due = fields.Float(allow_none=True)
    reference = fields.String(allow_none=True)
    status = fields.String()
    created_at = fields.String()


class RefundResponseSchema(Schema):
    id = fields.Integer()
    sale_id = fields.Integer()
    sale_item_id = fields.Integer(allow_none=True)
    quantity = fields.Integer()
    amount = fields.Float()
    reason = fields.String(allow_none=True)
    status = fields.String()
    processed_by_name = fields.String(allow_none=True)

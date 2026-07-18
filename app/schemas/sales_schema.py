from marshmallow import Schema, fields, validate


class SaleItemInputSchema(Schema):
    product_id = fields.Integer(required=True)
    variant_id = fields.Integer(required=False, allow_none=True)
    unit_id = fields.Integer(required=False, allow_none=True)
    quantity = fields.Integer(required=True, validate=validate.Range(min=1))
    discount_amount = fields.Decimal(required=False, places=2, as_string=False, load_default=0)
    discount_type = fields.String(required=False, allow_none=True,
                                   validate=validate.OneOf(["percentage", "fixed"]))
    discount_value = fields.Decimal(required=False, allow_none=True, places=2, as_string=False)
    discount_reason = fields.String(required=False, allow_none=True)


class PaymentInputSchema(Schema):
    method = fields.String(required=True, validate=validate.OneOf(
        ["cash", "card", "offline", "mobile_money", "wallet", "gift_card"]))
    amount = fields.Decimal(required=True, places=2, as_string=False, validate=validate.Range(min=0.01))
    amount_tendered = fields.Decimal(required=False, places=2, as_string=False, allow_none=True)
    reference = fields.String(required=False, allow_none=True)
    gift_card_code = fields.String(required=False, allow_none=True)


class SaleCreateSchema(Schema):
    items = fields.List(fields.Nested(SaleItemInputSchema), required=True, validate=validate.Length(min=1))
    payments = fields.List(fields.Nested(PaymentInputSchema), required=True, validate=validate.Length(min=1))
    customer_id = fields.Integer(required=False, allow_none=True)
    discount_amount = fields.Decimal(required=False, places=2, as_string=False, load_default=0)
    discount_reason = fields.String(required=False, allow_none=True)


class RefundCreateSchema(Schema):
    sale_item_id = fields.Integer(required=True)
    quantity = fields.Integer(required=True, validate=validate.Range(min=1))
    reason = fields.String(required=True, validate=validate.Length(min=1, max=255))
    as_store_credit = fields.Boolean(required=False, load_default=False)


class SaleResponseSchema(Schema):
    id = fields.Integer()
    receipt_number = fields.String()
    subtotal = fields.Float()
    tax_amount = fields.Float()
    discount_amount = fields.Float()
    total_amount = fields.Float()
    status = fields.String()
    cashier_name = fields.String(allow_none=True)
    customer_name = fields.String(allow_none=True)
    items = fields.List(fields.Dict())
    payments = fields.List(fields.Dict())
    created_at = fields.String()

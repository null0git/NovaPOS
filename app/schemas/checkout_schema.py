from marshmallow import Schema, fields, validate


class CheckoutStartSchema(Schema):
    terminal_id = fields.Integer(required=False, allow_none=True)
    customer_id = fields.Integer(required=False, allow_none=True)


class CheckoutItemSchema(Schema):
    product_id = fields.Integer(required=True)
    variant_id = fields.Integer(required=False, allow_none=True)
    unit_id = fields.Integer(required=False, allow_none=True)
    quantity = fields.Integer(required=True, validate=validate.Range(min=1))
    discount_amount = fields.Decimal(required=False, places=2, as_string=False, load_default=0)
    discount_type = fields.String(required=False, allow_none=True,
                                   validate=validate.OneOf(["percentage", "fixed"]))
    discount_value = fields.Decimal(required=False, allow_none=True, places=2, as_string=False)
    discount_reason = fields.String(required=False, allow_none=True)


class CheckoutSetItemsSchema(Schema):
    items = fields.List(fields.Nested(CheckoutItemSchema), required=True, validate=validate.Length(min=1))
    cart_discount_amount = fields.Decimal(required=False, places=2, as_string=False, load_default=0)
    cart_discount_reason = fields.String(required=False, allow_none=True)


class CustomerPaymentMethodSchema(Schema):
    method = fields.String(required=True, validate=validate.OneOf(["cash", "chapa", "offline"]))
    customer_email = fields.Email(required=False, allow_none=True)
    customer_name = fields.String(required=False, allow_none=True)


class ConfirmCashSchema(Schema):
    amount_tendered = fields.Decimal(required=False, allow_none=True, places=2, as_string=False)


class ConfirmOfflineSchema(Schema):
    reference = fields.String(required=False, allow_none=True)

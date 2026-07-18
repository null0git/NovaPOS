from marshmallow import Schema, fields, validate


class GiftCardIssueSchema(Schema):
    initial_value = fields.Decimal(required=True, places=2, as_string=False, validate=validate.Range(min=0.01))
    customer_id = fields.Integer(required=False, allow_none=True)
    expires_at = fields.DateTime(required=False, allow_none=True)
    card_type = fields.String(required=False, load_default="gift_card",
                               validate=validate.OneOf(["gift_card", "store_credit"]))


class GiftCardRechargeSchema(Schema):
    amount = fields.Decimal(required=True, places=2, as_string=False, validate=validate.Range(min=0.01))


class GiftCardRedeemSchema(Schema):
    amount = fields.Decimal(required=True, places=2, as_string=False, validate=validate.Range(min=0.01))
    sale_id = fields.Integer(required=False, allow_none=True)

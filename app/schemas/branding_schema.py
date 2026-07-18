from marshmallow import Schema, fields


class BrandingUpdateSchema(Schema):
    business_name = fields.String(required=False, allow_none=True)
    address = fields.String(required=False, allow_none=True)
    phone = fields.String(required=False, allow_none=True)
    email = fields.Email(required=False, allow_none=True)
    website = fields.String(required=False, allow_none=True)
    tax_number = fields.String(required=False, allow_none=True)


class TaxConfigUpdateSchema(Schema):
    tax_enabled = fields.Boolean(required=False)
    tax_name = fields.String(required=False)
    default_tax_rate = fields.Float(required=False)
    prices_include_tax = fields.Boolean(required=False)

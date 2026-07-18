from marshmallow import Schema, fields, validate


class UnitCreateSchema(Schema):
    unit_name = fields.String(required=True, validate=validate.Length(min=1, max=30))
    conversion_ratio = fields.Decimal(required=True, places=4, as_string=False, validate=validate.Range(min=0.0001))
    price = fields.Decimal(required=True, places=2, as_string=False, validate=validate.Range(min=0))
    barcode = fields.String(required=False, allow_none=True)


class UnitUpdateSchema(Schema):
    unit_name = fields.String(required=False)
    conversion_ratio = fields.Decimal(required=False, places=4, as_string=False)
    price = fields.Decimal(required=False, places=2, as_string=False)
    barcode = fields.String(required=False, allow_none=True)
    is_active = fields.Boolean(required=False)

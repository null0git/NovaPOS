from marshmallow import Schema, fields, validate


class DeviceCreateSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    device_type = fields.String(required=True, validate=validate.OneOf(
        ["customer_display", "receipt_printer", "barcode_scanner", "cash_drawer", "pos_terminal"]))
    identifier = fields.String(required=True, validate=validate.Length(min=1, max=100))
    ip_address = fields.String(required=False, allow_none=True)
    config = fields.Dict(required=False, allow_none=True)


class DeviceUpdateSchema(Schema):
    name = fields.String(required=False)
    ip_address = fields.String(required=False, allow_none=True)
    is_active = fields.Boolean(required=False)
    config = fields.Dict(required=False, allow_none=True)


class DeviceResponseSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    device_type = fields.String()
    identifier = fields.String()
    ip_address = fields.String(allow_none=True)
    is_active = fields.Boolean()
    last_seen_at = fields.String(allow_none=True)

from marshmallow import Schema, fields


class SessionResponseSchema(Schema):
    id = fields.Integer()
    user_id = fields.Integer()
    user_name = fields.String(allow_none=True)
    device_info = fields.String(allow_none=True)
    terminal_name = fields.String(allow_none=True)
    ip_address = fields.String(allow_none=True)
    revoked = fields.Boolean()
    created_at = fields.String()
    last_seen_at = fields.String(allow_none=True)
    expires_at = fields.String()

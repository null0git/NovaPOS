from marshmallow import Schema, fields, validate


class NotificationResponseSchema(Schema):
    id = fields.Integer()
    type = fields.String()
    title = fields.String()
    message = fields.String(allow_none=True)
    is_read = fields.Boolean()
    severity = fields.String()
    created_at = fields.String()


class NotificationCreateSchema(Schema):
    type = fields.String(required=True)
    title = fields.String(required=True, validate=validate.Length(min=1, max=150))
    message = fields.String(required=False, allow_none=True)
    severity = fields.String(required=False, load_default="info",
                              validate=validate.OneOf(["info", "warning", "critical"]))
    user_id = fields.Integer(required=False, allow_none=True)

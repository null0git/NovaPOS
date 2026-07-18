from marshmallow import Schema, fields


class SettingUpdateSchema(Schema):
    key = fields.String(required=True)
    value = fields.Raw(required=True)
    description = fields.String(required=False, allow_none=True)


class SettingResponseSchema(Schema):
    key = fields.String()
    value = fields.Raw()
    description = fields.String(allow_none=True)

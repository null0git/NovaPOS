from marshmallow import Schema, fields, validate


class UserCreateSchema(Schema):
    username = fields.String(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=False, allow_none=True)
    full_name = fields.String(required=True, validate=validate.Length(min=1, max=150))
    password = fields.String(required=True, validate=validate.Length(min=6))
    phone = fields.String(required=False, allow_none=True)
    role_name = fields.String(required=True)


class UserUpdateSchema(Schema):
    email = fields.Email(required=False, allow_none=True)
    full_name = fields.String(required=False, validate=validate.Length(min=1, max=150))
    phone = fields.String(required=False, allow_none=True)
    role_name = fields.String(required=False)
    is_active = fields.Boolean(required=False)


class UserResponseSchema(Schema):
    id = fields.Integer()
    username = fields.String()
    email = fields.String(allow_none=True)
    full_name = fields.String()
    phone = fields.String(allow_none=True)
    role = fields.String(allow_none=True)
    is_active = fields.Boolean()
    last_login_at = fields.String(allow_none=True)

from marshmallow import Schema, fields, validate


class LoginSchema(Schema):
    username = fields.String(required=True, validate=validate.Length(min=1))
    password = fields.String(required=True, validate=validate.Length(min=1))


class RefreshResponseSchema(Schema):
    access_token = fields.String()


class TokenResponseSchema(Schema):
    access_token = fields.String()
    refresh_token = fields.String()
    user = fields.Dict()


class ChangePasswordSchema(Schema):
    current_password = fields.String(required=True)
    new_password = fields.String(required=True, validate=validate.Length(min=6))


class RegisterUserSchema(Schema):
    username = fields.String(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=False, allow_none=True)
    full_name = fields.String(required=True, validate=validate.Length(min=1, max=150))
    password = fields.String(required=True, validate=validate.Length(min=6))
    phone = fields.String(required=False, allow_none=True)
    role_name = fields.String(required=True)

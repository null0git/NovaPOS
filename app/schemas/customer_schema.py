from marshmallow import Schema, fields, validate

from app.core.utils.validators import validate_phone


class CustomerCreateSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=150))
    email = fields.Email(required=False, allow_none=True)
    phone = fields.String(required=False, allow_none=True, validate=validate_phone)
    address = fields.String(required=False, allow_none=True)


class CustomerUpdateSchema(Schema):
    name = fields.String(required=False, validate=validate.Length(min=1, max=150))
    email = fields.Email(required=False, allow_none=True)
    phone = fields.String(required=False, allow_none=True, validate=validate_phone)
    address = fields.String(required=False, allow_none=True)
    is_active = fields.Boolean(required=False)


class CustomerResponseSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    email = fields.String(allow_none=True)
    phone = fields.String(allow_none=True)
    address = fields.String(allow_none=True)
    loyalty_points = fields.Integer()
    is_active = fields.Boolean()

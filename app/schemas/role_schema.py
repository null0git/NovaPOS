from marshmallow import Schema, fields, validate


class RoleCreateSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=2, max=50))
    description = fields.String(required=False, allow_none=True)
    permissions = fields.List(fields.String(), required=False, load_default=list)


class RoleUpdateSchema(Schema):
    description = fields.String(required=False, allow_none=True)
    permissions = fields.List(fields.String(), required=False)


class RoleResponseSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    description = fields.String(allow_none=True)
    permissions = fields.List(fields.String())

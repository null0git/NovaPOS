from marshmallow import Schema, fields, validate


class CategoryCreateSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    description = fields.String(required=False, allow_none=True)
    parent_id = fields.Integer(required=False, allow_none=True)


class CategoryUpdateSchema(Schema):
    name = fields.String(required=False, validate=validate.Length(min=1, max=100))
    description = fields.String(required=False, allow_none=True)
    parent_id = fields.Integer(required=False, allow_none=True)
    is_active = fields.Boolean(required=False)


class CategoryResponseSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    description = fields.String(allow_none=True)
    parent_id = fields.Integer(allow_none=True)
    is_active = fields.Boolean()

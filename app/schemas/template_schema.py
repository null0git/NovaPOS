from marshmallow import Schema, fields, validate


class ReceiptTemplateCreateSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    paper_width_mm = fields.Integer(required=False, load_default=80, validate=validate.OneOf([58, 80]))
    layout = fields.Dict(required=True)
    set_default = fields.Boolean(required=False, load_default=False)


class ReceiptTemplateUpdateSchema(Schema):
    name = fields.String(required=False)
    paper_width_mm = fields.Integer(required=False, validate=validate.OneOf([58, 80]))
    layout = fields.Dict(required=False)
    is_active = fields.Boolean(required=False)


class LabelTemplateCreateSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    label_size = fields.String(required=False, load_default="medium",
                                validate=validate.OneOf(["small", "medium", "large"]))
    layout = fields.Dict(required=True)
    set_default = fields.Boolean(required=False, load_default=False)


class LabelTemplateUpdateSchema(Schema):
    name = fields.String(required=False)
    label_size = fields.String(required=False, validate=validate.OneOf(["small", "medium", "large"]))
    layout = fields.Dict(required=False)
    is_active = fields.Boolean(required=False)

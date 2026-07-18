from marshmallow import Schema, fields, validate


class BulkBarcodeGenerateSchema(Schema):
    quantity = fields.Integer(required=True, validate=validate.Range(min=1, max=5000))
    batch_label = fields.String(required=False, allow_none=True)


class ManufacturerBarcodeScanSchema(Schema):
    code = fields.String(required=True, validate=validate.Length(min=1, max=100))


class LabelPrintSchema(Schema):
    barcode_ids = fields.List(fields.Integer(), required=True, validate=validate.Length(min=1))
    label_size = fields.String(required=False, load_default="medium",
                                validate=validate.OneOf(["small", "medium", "large"]))
    show_price = fields.Boolean(required=False, load_default=True)
    show_sku = fields.Boolean(required=False, load_default=True)

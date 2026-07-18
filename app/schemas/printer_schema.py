from marshmallow import Schema, fields, validate


class PrinterCreateSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    connection_type = fields.String(required=True, validate=validate.OneOf(["usb", "bluetooth", "network"]))
    identifier = fields.String(required=True, validate=validate.Length(min=1, max=150))
    ip_address = fields.String(required=False, allow_none=True)
    bluetooth_address = fields.String(required=False, allow_none=True)
    manufacturer = fields.String(required=False, allow_none=True)
    model = fields.String(required=False, allow_none=True)
    profile_type = fields.String(required=False, load_default="receipt",
                                  validate=validate.OneOf(["receipt", "label", "kitchen"]))


class PrinterUpdateSchema(Schema):
    name = fields.String(required=False, validate=validate.Length(min=1, max=100))
    ip_address = fields.String(required=False, allow_none=True)
    is_active = fields.Boolean(required=False)


class PrinterResponseSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    connection_type = fields.String()
    identifier = fields.String()
    ip_address = fields.String(allow_none=True)
    bluetooth_address = fields.String(allow_none=True)
    manufacturer = fields.String(allow_none=True)
    model = fields.String(allow_none=True)
    profile_type = fields.String()
    status = fields.String()
    paper_status = fields.String(allow_none=True)
    is_default = fields.Boolean()
    is_active = fields.Boolean()
    last_seen_at = fields.String(allow_none=True)


class DiscoveredPrinterSchema(Schema):
    """A printer reported by a client-side discovery agent (browser/desktop app with USB/BT/mDNS access)."""
    name = fields.String(required=True)
    connection_type = fields.String(required=True, validate=validate.OneOf(["usb", "bluetooth", "network"]))
    identifier = fields.String(required=True)
    ip_address = fields.String(required=False, allow_none=True)
    bluetooth_address = fields.String(required=False, allow_none=True)
    manufacturer = fields.String(required=False, allow_none=True)
    model = fields.String(required=False, allow_none=True)


class PrinterDiscoverSchema(Schema):
    """Payload submitted by the client's local discovery agent after it scans USB/Bluetooth/network."""
    discovered = fields.List(fields.Nested(DiscoveredPrinterSchema), required=False, load_default=list)

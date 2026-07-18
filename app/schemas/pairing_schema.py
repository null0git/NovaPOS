from marshmallow import Schema, fields


class GeneratePairingCodeSchema(Schema):
    terminal_id = fields.Integer(required=True)
    server_address = fields.String(required=False, allow_none=True)


class RedeemPairingCodeSchema(Schema):
    code = fields.String(required=True)
    display_identifier = fields.String(required=True)
    display_name = fields.String(required=False, load_default="Customer Display")

"""Customer-display pairing endpoints: discovery, pairing code + QR generation, redemption."""
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.security.permissions import permission_required
from app.core.utils.response import success_response
from app.schemas.pairing_schema import GeneratePairingCodeSchema, RedeemPairingCodeSchema
from app.services.pairing_service import PairingService

blp = Blueprint("pairing", __name__, url_prefix="/api/v1/pairing",
                description="Customer display discovery & pairing")


@blp.route("/discover-terminals")
class DiscoverTerminalsResource(MethodView):
    @blp.doc(security=[])
    def get(self):
        """Automatic local-network discovery: lists recently-active POS terminals."""
        terminals = PairingService().discover_terminals()
        return success_response([t.to_dict() for t in terminals])


@blp.route("/generate-code")
class GeneratePairingCodeResource(MethodView):
    @jwt_required()
    @permission_required("sales.create", "sales.manage", "settings.manage")
    @blp.arguments(GeneratePairingCodeSchema)
    def post(self, data):
        """Cashier generates a code (+ QR) on the POS terminal for the customer display to redeem."""
        result = PairingService().generate_pairing_code(**data)
        return success_response(result, "Pairing code generated", 201)


@blp.route("/redeem")
class RedeemPairingCodeResource(MethodView):
    @blp.doc(security=[])
    @blp.arguments(RedeemPairingCodeSchema)
    def post(self, data):
        """Called by the customer display (unauthenticated) with the code it was given."""
        result = PairingService().redeem_pairing_code(**data)
        return success_response(result, "Paired successfully")

"""Gift cards & store credit endpoints."""
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.core.middleware.auth_middleware import current_user_id
from app.core.security.permissions import permission_required
from app.core.utils.response import success_response
from app.schemas.gift_card_schema import GiftCardIssueSchema, GiftCardRechargeSchema, GiftCardRedeemSchema
from app.services.gift_card_service import GiftCardService

blp = Blueprint("gift_cards", __name__, url_prefix="/api/v1/gift-cards", description="Gift cards & store credit")


@blp.route("")
class GiftCardIssueResource(MethodView):
    @jwt_required()
    @permission_required("sales.manage", "customers.manage")
    @blp.arguments(GiftCardIssueSchema)
    def post(self, data):
        card = GiftCardService().issue(current_user_id(), **data)
        return success_response(card.to_dict(), "Gift card issued", 201)


@blp.route("/customer/<int:customer_id>")
class GiftCardsForCustomerResource(MethodView):
    @jwt_required()
    def get(self, customer_id):
        cards = GiftCardService().list_for_customer(customer_id)
        return success_response([c.to_dict() for c in cards])


@blp.route("/<string:code>")
class GiftCardDetailResource(MethodView):
    @jwt_required()
    def get(self, code):
        card = GiftCardService().get_by_code(code)
        return success_response(card.to_dict())

    @jwt_required()
    @permission_required("sales.manage", "customers.manage")
    def delete(self, code):
        card = GiftCardService().deactivate(current_user_id(), code)
        return success_response(card.to_dict(), "Gift card deactivated")


@blp.route("/<string:code>/balance")
class GiftCardBalanceResource(MethodView):
    @jwt_required()
    def get(self, code):
        return success_response(GiftCardService().get_balance(code))


@blp.route("/<string:code>/recharge")
class GiftCardRechargeResource(MethodView):
    @jwt_required()
    @permission_required("sales.create", "sales.manage")
    @blp.arguments(GiftCardRechargeSchema)
    def post(self, data, code):
        card = GiftCardService().recharge(current_user_id(), code, data["amount"])
        return success_response(card.to_dict(), "Gift card recharged")


@blp.route("/<string:code>/redeem")
class GiftCardRedeemResource(MethodView):
    @jwt_required()
    @permission_required("sales.create", "sales.manage")
    @blp.arguments(GiftCardRedeemSchema)
    def post(self, data, code):
        """Manually redeem without going through /sales — normally redemption happens
        automatically when 'gift_card' is used as a payment method during checkout."""
        card = GiftCardService().redeem(current_user_id(), code, data["amount"], data.get("sale_id"))
        return success_response(card.to_dict(), "Gift card redeemed")


@blp.route("/<string:code>/transactions")
class GiftCardTransactionsResource(MethodView):
    @jwt_required()
    def get(self, code):
        transactions = GiftCardService().transaction_history(code)
        return success_response([t.to_dict() for t in transactions])

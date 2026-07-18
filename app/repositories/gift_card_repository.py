from app.models.gift_card import GiftCard, GiftCardTransaction
from app.repositories.base_repository import BaseRepository
from app.extensions import db


class GiftCardRepository(BaseRepository):
    model = GiftCard

    def get_by_code(self, code):
        return GiftCard.query.filter_by(code=code).first()

    def code_exists(self, code):
        return GiftCard.query.filter_by(code=code).first() is not None

    def get_for_customer(self, customer_id):
        return GiftCard.query.filter_by(customer_id=customer_id)

    def add_transaction(self, **kwargs):
        txn = GiftCardTransaction(**kwargs)
        db.session.add(txn)
        return txn

    def get_transactions(self, gift_card_id):
        return GiftCardTransaction.query.filter_by(gift_card_id=gift_card_id).order_by(
            GiftCardTransaction.created_at.desc()
        )

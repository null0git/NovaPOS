from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.payment import Payment
from app.models.refund import Refund
from app.repositories.base_repository import BaseRepository
from app.extensions import db


class SalesRepository(BaseRepository):
    model = Sale

    def get_by_receipt_number(self, receipt_number):
        return Sale.query.filter_by(receipt_number=receipt_number).first()

    def receipt_number_exists(self, receipt_number):
        return Sale.query.filter_by(receipt_number=receipt_number).first() is not None

    def get_between(self, start, end):
        return Sale.query.filter(Sale.created_at >= start, Sale.created_at <= end)

    def get_by_cashier(self, cashier_id):
        return Sale.query.filter_by(cashier_id=cashier_id)

    def get_by_customer(self, customer_id):
        return Sale.query.filter_by(customer_id=customer_id)

    def add_item(self, **kwargs):
        item = SaleItem(**kwargs)
        db.session.add(item)
        return item

    def add_payment(self, **kwargs):
        payment = Payment(**kwargs)
        db.session.add(payment)
        return payment

    def add_refund(self, **kwargs):
        refund = Refund(**kwargs)
        db.session.add(refund)
        db.session.commit()
        return refund

    def get_sale_item(self, sale_item_id):
        return SaleItem.query.get(sale_item_id)

from app.models.customer import Customer
from app.repositories.base_repository import BaseRepository


class CustomerRepository(BaseRepository):
    model = Customer

    def get_by_email(self, email):
        return Customer.query.filter_by(email=email).first()

    def get_by_phone(self, phone):
        return Customer.query.filter_by(phone=phone).first()

    def email_exists(self, email, exclude_id=None):
        query = Customer.query.filter_by(email=email)
        if exclude_id:
            query = query.filter(Customer.id != exclude_id)
        return query.first() is not None

    def phone_exists(self, phone, exclude_id=None):
        query = Customer.query.filter_by(phone=phone)
        if exclude_id:
            query = query.filter(Customer.id != exclude_id)
        return query.first() is not None

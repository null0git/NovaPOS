"""Business logic for customer profiles and purchase history."""
from app.core.middleware.error_handler import ConflictError, NotFoundError
from app.extensions import db
from app.repositories.customer_repository import CustomerRepository
from app.services.audit_service import AuditService


class CustomerService:
    def __init__(self):
        self.repo = CustomerRepository()
        self.audit_service = AuditService()

    def list_customers(self, active_only=False):
        query = self.repo.get_all()
        if active_only:
            query = query.filter_by(is_active=True)
        return query

    def get_customer(self, customer_id):
        customer = self.repo.get_by_id(customer_id)
        if not customer:
            raise NotFoundError("Customer not found.")
        return customer

    def create_customer(self, actor_id, name, email=None, phone=None, address=None):
        if email and self.repo.email_exists(email):
            raise ConflictError("A customer with this email already exists.")
        if phone and self.repo.phone_exists(phone):
            raise ConflictError("A customer with this phone number already exists.")
        customer = self.repo.create(name=name, email=email, phone=phone, address=address)
        self.audit_service.log(actor_id, "customer.create", "customer", customer.id)
        return customer

    def update_customer(self, actor_id, customer_id, **fields):
        customer = self.get_customer(customer_id)
        email = fields.get("email")
        phone = fields.get("phone")
        if email and self.repo.email_exists(email, exclude_id=customer_id):
            raise ConflictError("A customer with this email already exists.")
        if phone and self.repo.phone_exists(phone, exclude_id=customer_id):
            raise ConflictError("A customer with this phone number already exists.")
        for key, value in fields.items():
            if value is not None:
                setattr(customer, key, value)
        db.session.commit()
        self.audit_service.log(actor_id, "customer.update", "customer", customer.id, details=fields)
        return customer

    def deactivate_customer(self, actor_id, customer_id):
        customer = self.get_customer(customer_id)
        customer.is_active = False
        db.session.commit()
        self.audit_service.log(actor_id, "customer.deactivate", "customer", customer.id)
        return customer

    def purchase_history(self, customer_id):
        customer = self.get_customer(customer_id)
        return customer.sales

    def add_loyalty_points(self, customer_id, points):
        customer = self.get_customer(customer_id)
        customer.loyalty_points += points
        db.session.commit()
        return customer

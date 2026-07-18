from app.models.printer import Printer
from app.repositories.base_repository import BaseRepository
from app.extensions import db


class PrinterRepository(BaseRepository):
    model = Printer

    def get_by_identifier(self, identifier):
        return Printer.query.filter_by(identifier=identifier).first()

    def identifier_exists(self, identifier, exclude_id=None):
        query = Printer.query.filter_by(identifier=identifier)
        if exclude_id:
            query = query.filter(Printer.id != exclude_id)
        return query.first() is not None

    def get_default(self):
        return Printer.query.filter_by(is_default=True, is_active=True).first()

    def clear_default(self):
        Printer.query.filter_by(is_default=True).update({"is_default": False})
        db.session.commit()

    def get_active(self):
        return Printer.query.filter_by(is_active=True)

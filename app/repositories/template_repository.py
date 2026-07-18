from app.models.templates import ReceiptTemplate, LabelTemplate
from app.repositories.base_repository import BaseRepository
from app.extensions import db


class ReceiptTemplateRepository(BaseRepository):
    model = ReceiptTemplate

    def get_default(self):
        return ReceiptTemplate.query.filter_by(is_default=True, is_active=True).first()

    def clear_default(self):
        ReceiptTemplate.query.filter_by(is_default=True).update({"is_default": False})
        db.session.commit()


class LabelTemplateRepository(BaseRepository):
    model = LabelTemplate

    def get_default(self):
        return LabelTemplate.query.filter_by(is_default=True, is_active=True).first()

    def clear_default(self):
        LabelTemplate.query.filter_by(is_default=True).update({"is_default": False})
        db.session.commit()

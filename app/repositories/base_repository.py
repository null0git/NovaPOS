"""Generic repository base class: pure data access, no business rules."""
from app.extensions import db


class BaseRepository:
    model = None

    def get_by_id(self, id_):
        return self.model.query.get(id_)

    def get_all(self):
        return self.model.query

    def create(self, **kwargs):
        instance = self.model(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance

    def add(self, instance):
        db.session.add(instance)
        db.session.commit()
        return instance

    def update(self, instance, **kwargs):
        for key, value in kwargs.items():
            setattr(instance, key, value)
        db.session.commit()
        return instance

    def delete(self, instance):
        db.session.delete(instance)
        db.session.commit()

    def flush(self):
        db.session.flush()

    def commit(self):
        db.session.commit()

    def rollback(self):
        db.session.rollback()

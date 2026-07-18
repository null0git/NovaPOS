from app.models.category import Category
from app.repositories.base_repository import BaseRepository


class CategoryRepository(BaseRepository):
    model = Category

    def get_by_name(self, name):
        return Category.query.filter_by(name=name).first()

    def name_exists(self, name, exclude_id=None):
        query = Category.query.filter_by(name=name)
        if exclude_id:
            query = query.filter(Category.id != exclude_id)
        return query.first() is not None

    def get_active(self):
        return Category.query.filter_by(is_active=True)

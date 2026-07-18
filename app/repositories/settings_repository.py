from app.models.settings import Setting
from app.repositories.base_repository import BaseRepository
from app.extensions import db


class SettingsRepository(BaseRepository):
    model = Setting

    def get_by_key(self, key):
        return Setting.query.filter_by(key=key).first()

    def set_value(self, key, value, description=None):
        setting = self.get_by_key(key)
        if setting:
            setting.value = value
            if description:
                setting.description = description
        else:
            setting = Setting(key=key, value=value, description=description)
            db.session.add(setting)
        db.session.commit()
        return setting

    def get_all_as_dict(self):
        return {s.key: s.value for s in Setting.query.all()}

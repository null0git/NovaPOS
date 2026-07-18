from app.models.device import Device
from app.repositories.base_repository import BaseRepository


class DeviceRepository(BaseRepository):
    model = Device

    def get_by_identifier(self, identifier):
        return Device.query.filter_by(identifier=identifier).first()

    def identifier_exists(self, identifier, exclude_id=None):
        query = Device.query.filter_by(identifier=identifier)
        if exclude_id:
            query = query.filter(Device.id != exclude_id)
        return query.first() is not None

    def get_by_type(self, device_type):
        return Device.query.filter_by(device_type=device_type)

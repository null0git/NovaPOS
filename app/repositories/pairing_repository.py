from app.models.pairing_code import PairingCode
from app.repositories.base_repository import BaseRepository


class PairingRepository(BaseRepository):
    model = PairingCode

    def get_by_code(self, code):
        return PairingCode.query.filter_by(code=code).first()

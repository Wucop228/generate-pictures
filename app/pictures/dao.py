from app.core.base_dao import BaseDAO
from app.pictures.models import Picture

class PicturesDAO(BaseDAO):
    model = Picture
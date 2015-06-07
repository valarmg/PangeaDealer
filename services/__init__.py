from db import PangeaDb
from db.PangeaDb2 import PangeaDb2


class PangeaDbServiceBase(object):
    def __init__(self, db: PangeaDb2):
        self.db = db


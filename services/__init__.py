from db import PangeaDb


class PangeaDbServiceBase(object):
    def __init__(self, db: PangeaDb):
        self.db = db


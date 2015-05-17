from db import PangeaDb


class PangeaDbServiceBase(object):
    def __init__(self, db):
        self.db = db


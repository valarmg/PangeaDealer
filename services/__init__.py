class PangeaDbServiceBase(object):
    def __init__(self, db, client_manager):
        self.db = db
        self.client_manager = client_manager


import logging
from services import PangeaDbServiceBase

logger = logging.getLogger(__name__)


class DealerService(PangeaDbServiceBase):
    def __init__(self, db):
        super().__init__(db)

    def deal_hand(self, table_id):
        logging.debug("deal_hand, table_id: {0}".format(table_id))

        table = self.db.table_get_by_id(table_id)

        # TODO: Do deal?
        # TODO: Update mechanism?
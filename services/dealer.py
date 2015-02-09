import logging
from utils.messages import PangeaMessage
from services import PangeaDbServiceBase

logger = logging.getLogger(__name__)


class DealerService(PangeaDbServiceBase):
    def __init__(self, db, client_manager):
        super().__init__(db, client_manager)

    def deal_hand(self, table_id):
        logging.debug("deal_hand, table_id: {0}".format(table_id))

        table = self.db.table_get_by_id(table_id)

        # TODO: Deal handle?

        self.fire_table_update(table)

    def fire_table_update(self, table):
        logger.debug("fire_table_update: {0}".format(table.table_id))
        message = PangeaMessage(table_id=table.table_id)

        for seat in table.seats_array:
            client = self.client_manager.get_client_by_player_name(seat.name)
            if client is not None:
                client.send_message(message)
import logging

from utils.messages import PangeaMessage
from services import PangeaDbServiceBase
import models

logger = logging.getLogger(__name__)


class TableService(PangeaDbServiceBase):
    def __init__(self, db, client_manager):
        super().__init__(db, client_manager)

    def create_table(self, lobby_id, name):
        logger.debug("create_table, lobby_id: {0}, name: {1}".format(lobby_id, name))
        table = {"lobby_id": lobby_id, "name": name}
        self.db.table_create(table)
        return table

    def join_table(self, table_id, player_id, seat_number):
        logger.debug("join_table, table_id: {0}, player_id: {1}, seat_number".format(table_id, player_id, seat_number))

        table = self.db.table_get_by_id(table_id)
        player = self.db.player_get_by_id(player_id)

        seat = models.Seat(player.id, player.name, seat_number)
        self.db.player_join_table(table_id, seat)
        self.fire_table_update(table)

    def leave_table(self, table_id, player_id):
        logger.debug("leave_table, table_id: {0}, player: {1}", table_id, player_id)

        table = self.db.table_get_by_id(table_id)
        self.db.player_leave_table(table_id, player_id)
        self.fire_table_update(table)

    def get_tables(self, client, lobby_id):
        logger.debug("get_tables")

        tables = self.db.table_get_by_lobby_id(lobby_id)

        data = []
        for table in tables:
            data.append(models.Table.from_db(table))

        message = PangeaMessage(tables=data)
        client.send_message(message)

    def get_table(self, client, table_id):
        logger.debug("get_table, table_id: {0}".format(table_id))

        table = self.db.table_get_by_id(table_id)
        model = models.Table.from_db(table)

        message = PangeaMessage(table=model)
        client.send_message(message)

    def fire_table_update(self, table):
        logger.debug("fire_table_update: {0}".format(table.table_id))
        message = PangeaMessage(table_id=table.table_id)

        for seat in table.seats_array:
            client = self.client_manager.get_client_by_player_name(seat.name)
            if client is not None:
                client.send_message(message)
import logging

from utils.messages import PangeaMessage
from services import PangeaDbServiceBase
from models import *
from utils.errors import PangeaException, PangaeaDealerErrorCodes
from modules.dealer import DealerModule

logger = logging.getLogger(__name__)


class TableService(PangeaDbServiceBase):
    def __init__(self, db):
        super().__init__(db)
        self.dealer_module = DealerModule(db)

    def create_table(self, lobby_id, name):
        logger.debug("create_table, lobby_id: {0}, name: {1}".format(lobby_id, name))
        table = self.db.table_create(lobby_id, name)
        return PangeaMessage(table=table)

    def join_table(self, table_id, player_id, seat_number, stack):
        logger.debug("join_table, table_id: {0}, player_id: {1}, seat_number: {2}, stack: {3}"
                     .format(table_id, player_id, seat_number, stack))

        if not table_id:
            raise PangeaException.missing_field("table_id")
        if not player_id:
            raise PangeaException.missing_field("player_id")
        if not seat_number:
            raise PangeaException.missing_field("seat_number")

        player = self.db.player_get_by_id(player_id)

        table = self.db.table_get_by_id(table_id)
        exists = table.seats and any(x.seat_number == seat_number for x in table.seats)
        if exists:
            raise PangeaException(PangaeaDealerErrorCodes.AlreadyExists, "Seat was been taken by another player")

        playing = True if table.current_round == Round.NA else False
        self.db.player_join_table(table_id, player_id, player.username, seat_number, stack, playing)

        message = ChatMessage.PLAYER_TABLE_JOIN.format(player.username)
        self.db.chat_create(message, table_id)
        self.db.event_create(TableEvent.PLAYER_JOIN_TABLE, table_id, seat_number, player.username)

        self.dealer_module.continue_hand(table)

        return PangeaMessage()

    def leave_table(self, table_id, player_id):
        logger.debug("leave_table, table_id: {0}, player_id: {1}".format(table_id, player_id))

        if not table_id:
            raise PangeaException.missing_field("table_id")
        if not player_id:
            raise PangeaException.missing_field("player_id")

        table = self.db.table_get_by_id(table_id)
        player = self.db.player_get_by_id(player_id)
        self.db.player_leave_table(table_id, player_id)

        player_seat_number = ""
        for seat in table.seats:
            if seat.player_id == player_id:
                player_seat_number = seat.seat_number
                break

        message = ChatMessage.PLAYER_TABLE_LEAVE.format(player.username)
        self.db.chat_create(message, table_id)
        self.db.event_create(TableEvent.PLAYER_LEAVE_TABLE, table_id, player_seat_number, player.username)

        self.dealer_module.continue_hand(table)

        return PangeaMessage()

    def get_tables(self, lobby_id):
        logger.debug("get_tables, lobby_id: {0}".format(lobby_id))

        # TODO: Only your own cards should be returned. The deck should not be returned, or any other player's cards
        # TODO: Get tables should probably only return a subset of the table information, maybe just the
        # TODO: lobby id, table id and the number of players
        if lobby_id:
            tables = self.db.table_get_by_lobby_id(lobby_id)
        else:
            tables = self.db.table_get_all()

        data = []
        for table in tables:
            data.append(Table.from_db(table))

        return PangeaMessage(tables=data)

    def get_table(self, table_id):
        logger.debug("get_table, table_id: {0}".format(table_id))

        # TODO: Only your own cards should be returned. The deck should not be returned, or any other player's cards
        table = self.db.table_get_by_id(table_id)
        model = Table.from_db(table)

        return PangeaMessage(table=model)

    def get_table_status(self, table_id, player_id, last_check):
        logger.debug("get_table_status, table_id: {0}, player_id: {1}, last_check: {2}"
                     .format(table_id, player_id, last_check))

        # TODO: This should properly return a 304 error if the table has been updated, no events have happened
        # TODO: and no chats have been sent

        # TODO: Only your own cards should be returned. The deck should not be returned, or any other player's cards
        table = self.db.table_get_by_id(table_id)

        events = None
        if last_check:
            # Only return
            events = self.db.event_get_by_table_id(table_id, last_check)

        chats = self.db.chat_get_by_table_id(table_id, last_check)

        return PangeaMessage(table=table, events=events, chats=chats)

    def kick_timed_out_players(self):
        logger.debug("kick_timed_out_players")

        tables = self.db.table_get_all()
        for table in tables:
            self.dealer_module.kick_timed_out_players(table)
            self.dealer_module.continue_hand(table)
import logging

from utils.messages import PangeaMessage
from services import PangeaDbServiceBase
from models import *
from utils.errors import PangeaException, PangaeaDealerErrorCodes
from db import PangeaDb
from modules import DealerModule

logger = logging.getLogger(__name__)


class TableService(PangeaDbServiceBase):
    def __init__(self, db):
        super().__init__(db)
        self.dealer_module = DealerModule(db)

    def create_table(self, lobby_id, name, use_default):
        logger.debug("create_table, lobby_id: {0}, name: {1}, use_default: {2}".format(lobby_id, name, use_default))

        if use_default:
            table = self.db.table.get_default()
            if not table:
                logger.debug("Default table does not exist, creating automatically")
                lobby = self.db.lobby.get_default()
                if not lobby:
                    logger.debug("Default lobby does not exist, creating automatically")
                    lobby = self.db.lobby.create("Default Lobby", True)

                table = self.db.table.create(lobby.id, "Default Table", True)
        else:
            table = self.db.table.create(lobby_id, name)

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

        player = self.db.player.get_by_id(player_id)
        table = self.db.table.get_by_id(table_id)

        self.dealer_module.join_table(table, player, seat_number, stack)
        self.db.table.update(table)

        return PangeaMessage()

    def leave_table(self, table_id, player_id):
        logger.debug("leave_table, table_id: {0}, player_id: {1}".format(table_id, player_id))

        if not table_id:
            raise PangeaException.missing_field("table_id")
        if not player_id:
            raise PangeaException.missing_field("player_id")

        table = self.db.table.get_by_id(table_id)
        player = self.db.player.get_by_id(player_id)

        self.dealer_module.leave_table(table, player)
        self.db.table.update(table)

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

        table = self.db.table.get_by_id(table_id)

        events = None
        chats = None
        if last_check:
            # Only new events/chats are returned
            events = self.db.event.get_by_table_id(table_id, last_check)
            chats = self.db.chat.get_by_table_id(table_id, last_check)

        table.deck_cards = None
        player_seat = table.organised_seats.get_seat_by_player_id(player_id)

        # Unless we on the last round (river or everyone has folded),
        # we should not return the cards of other players
        for seat in table.seats:
            if seat.player_id != player_id:
                if table.flip_cards:
                    seat.hole_cards = seat.flipped_cards
                else:
                    seat.hole_cards = None
            seat.flipped_cards = None

        return PangeaMessage(table=table, player_seat=player_seat, events=events, chats=chats)

    def delete_table(self, table_id):
        logger.debug("delete_table, table_id: {0}", table_id)

        if table_id:
            self.db.table.delete(table_id)
        else:
            self.db.table.delete_all()

        return PangeaMessage()

    def delete_default_table(self):
        logger.debug("delete_default_table, table_id: {0}")

        table = self.db.table.get_default()
        if table:
            self.db.table.delete(table.id)
        return PangeaMessage()

    def check_tables(self):
        tables = self.db.table.get_all()
        for table in tables:
            kicked_out_players = self.dealer_module.kick_timed_out_players(table)
            restarted_game = self.dealer_module.restart_table(table)

            if kicked_out_players or restarted_game:
                self.db.table.update(table)
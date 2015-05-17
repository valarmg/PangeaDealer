import logging
from services import PangeaDbServiceBase
from utils.messages import PangeaMessage
from utils.errors import PangeaException, PangaeaDealerErrorCodes
from models import *
from modules.dealer import DealerModule
from modules.bet import BetModule
import datetime


class BetService(PangeaDbServiceBase):
    log = logging.getLogger(__name__)

    def __init__(self, db):
        super().__init__(db)
        self.dealer_module = DealerModule(db)
        self.bet_module = BetModule(db)

    def fold(self, table_id, player_id):
        self.log.debug("fold, table_id: {0}, player_id: {1}".format(table_id, player_id))

        # Validate and retrieve data from the database
        if table_id is None:
            raise PangeaException.missing_field("table_id")
        if player_id is None:
            raise PangeaException.missing_field("player_id")

        table = self.db.table_get_by_id(table_id)
        player = self.db.player_get_by_id(player_id)

        self.bet_module.fold(table, player)
        self.dealer_module.continue_hand(table)

        # Return the updated table
        table = self.db.table_get_by_id(table_id)
        return PangeaMessage(table=table)

    def check(self, table_id, player_id):
        self.log.debug("check, table_id: {0}, player_id: {1}".format(table_id, player_id))

        if table_id is None:
            raise PangeaException.missing_field("table_id")
        if player_id is None:
            raise PangeaException.missing_field("player_id")

        table = self.db.table_get_by_id(table_id)
        player = self.db.player_get_by_id(player_id)

        self.bet_module.check(table, player)
        self.dealer_module.continue_hand(table)

        # Return the updated table
        table = self.db.table_get_by_id(table_id)
        return PangeaMessage(table=table)

    def bet(self, table_id, player_id, amount, is_raise):
        self.log.debug("bet, table_id: {0}, player_id: {1}, amount: {2}, is_raise: {3}",
                       table_id, player_id, amount, is_raise)

        if table_id is None:
            raise PangeaException.missing_field("table_id")
        if player_id is None:
            raise PangeaException.missing_field("player_id")
        if amount is None:
            raise PangeaException.missing_field("amount")

        table = self.db.table_get_by_id(table_id)
        player = self.db.player_get_by_id(player_id)

        self.bet_module.bet(table, player, amount, is_raise)
        self.dealer_module.continue_hand(table)

        table = self.db.table_get_by_id(table_id)
        return PangeaMessage(table=table)
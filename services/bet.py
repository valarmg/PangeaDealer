import logging
from services import PangeaDbServiceBase
from utils.messages import PangeaMessage
from utils.errors import PangeaException, PangaeaDealerErrorCodes
from models import *
from modules import DealerModule2
from modules import BettingModule2
import datetime
from db.PangeaDb2 import PangeaDb2


class BetService(PangeaDbServiceBase):
    log = logging.getLogger(__name__)

    def __init__(self, db: PangeaDb2):
        super().__init__(db)
        self.dealer_module = DealerModule2(db)
        self.bet_module = BettingModule2(db)

    def fold(self, table_id, player_id):
        self.log.debug("fold, table_id: {0}, player_id: {1}".format(table_id, player_id))

        if table_id is None:
            raise PangeaException.missing_field("table_id")
        if player_id is None:
            raise PangeaException.missing_field("player_id")

        table = self.db.table.get_by_id(table_id)
        player = self.db.player.get_by_id(player_id)

        self.bet_module.fold(table, player)
        self.dealer_module.continue_hand(table)
        self.db.table.update(table)

        return PangeaMessage(table=table)

    def check(self, table_id, player_id):
        self.log.debug("check, table_id: {0}, player_id: {1}".format(table_id, player_id))

        if table_id is None:
            raise PangeaException.missing_field("table_id")
        if player_id is None:
            raise PangeaException.missing_field("player_id")

        table = self.db.table.get_by_id(table_id)
        player = self.db.player.get_by_id(player_id)

        self.bet_module.check(table, player)
        self.dealer_module.continue_hand(table)
        self.db.table.update(table)

        return PangeaMessage(table=table)

    def bet(self, table_id, player_id, amount):
        self.log.debug("bet, table_id: {0}, player_id: {1}, amount: {2}".format(table_id, player_id, amount))

        if table_id is None:
            raise PangeaException.missing_field("table_id")
        if player_id is None:
            raise PangeaException.missing_field("player_id")
        if amount is None:
            raise PangeaException.missing_field("amount")

        table = self.db.table.get_by_id(table_id)
        player = self.db.player.get_by_id(player_id)

        # TODO:
        # Rather than having a is_raise flag sent in the request, determine if
        # it's a raise by checking if it is over the current bet

        self.bet_module.bet(table, player, amount)
        self.dealer_module.continue_hand(table)
        self.db.table.update(table)

        return PangeaMessage(table=table)
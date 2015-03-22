import logging
from services import PangeaDbServiceBase
from utils.messages import PangeaMessage
from utils.errors import PangeaException, PangaeaDealerErrorCodes
from models import *


class BetService(PangeaDbServiceBase):
    def __init__(self, db):
        super().__init__(db)
        self.log = logging.getLogger(__name__)

    def bet(self, table_id, player_id, amount):
        if table_id is None:
            raise PangeaException.missing_field("table_id")
        if player_id is None:
            raise PangeaException.missing_field("player_id")
        if amount is None:
            raise PangeaException.missing_field("amount")

        table = self.db.table_get_by_id(table_id)
        player = self.db.player_get_by_id(player_id)

        bet = self.db.bet(table_id, player_id, amount)

        self.db.chat_create(ChatMessage.PLAYER_TABLE_JOIN.format(player.player_name), table_id)
        self.db.event_create(TableEvent.PLAYER_BET.format(player.player_name, amount), table_id,
                             player_id, player.player_name, bet=bet)
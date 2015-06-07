import logging
from services import PangeaDbServiceBase
from utils.messages import PangeaMessage
from utils.errors import PangeaException, PangaeaDealerErrorCodes
from db import PangeaDb


class ChatService(PangeaDbServiceBase):
    def __init__(self, db):
        super().__init__(db)
        self.log = logging.getLogger(__name__)

    def chat(self, table_id, player_id, chat_message):
        if table_id is None:
            raise PangeaException.missing_field("table_id")
        if player_id is None:
            raise PangeaException.missing_field("player_id")
        if chat_message is None:
            raise PangeaException.missing_field("chat_message")

        player = self.db.player_get_by_id(player_id)
        self.db.chat_create("{0}: {1}".format(player.get("username", ""), chat_message), table_id)
        return PangeaMessage()
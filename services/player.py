import logging
from services import PangeaDbServiceBase
from utils.messages import PangeaMessage
from utils.errors import PangeaException, PangaeaDealerErrorCodes
import models
from db import PangeaDb


logger = logging.getLogger(__name__)


class PlayerService(PangeaDbServiceBase):
    def __init__(self, db):
        super().__init__(db)

    def create_player(self, username):
        logger.debug("create_player, username: {0}".format(username))

        if username is None or username.isspace():
            raise PangeaException.missing_field("username")

        player = self.db.player.create(username)
        return PangeaMessage(player=player)

    def get_players(self, table_id):
        logger.debug("get_players, table_id: {0}".format(table_id))

        if table_id:
            players = self.db.player_get_by_table_id(table_id)
        else:
            players = self.db.player_get_all()

        return PangeaMessage(players=players)

    def get_player(self, player_id):
        logger.debug("get_player, player_id: {0}".format(player_id))

        if player_id:
            player = self.db.player_get_by_id(player_id)
        else:
            raise PangeaException.missing_field("player_id")

        return PangeaMessage(player=player)
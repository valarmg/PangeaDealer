import logging
from services import PangeaDbServiceBase
from utils.messages import PangeaMessage
from utils.errors import PangeaException, PangaeaDealerErrorCodes
import models

logger = logging.getLogger(__name__)


class PlayerService(PangeaDbServiceBase):
    def __init__(self, db):
        super().__init__(db)

    def create_player(self, username):
        logger.debug("create_player, username: {0}".format(username))

        if username is None or username.isspace():
            raise PangeaException.missing_field("username")

        player = {"username": username}
        self.db.player_create(player)

        model = models.Player()
        model.from_dict(player)

        return PangeaMessage(player=model)

    def get_players(self, table_id):
        logger.debug("get_players, table_id: {0}".format(table_id))

        if table_id:
            documents = self.db.players_get_by_table_id(table_id)
        else:
            documents = self.db.players_get_all()

        data = []
        for lobby in documents:
            data.append(models.Player.from_db(lobby))

        return PangeaMessage(players=data)

    def get_player(self, player_id=None, username=None):
        logger.debug("get_player, player_id: {0}, username: {1}".format(player_id, username))

        if player_id:
            player = self.db.player_get_by_id(player_id)
        elif username:
            player = self.db.player_get_by_username(username)
        else:
            raise PangeaException.missing_field("player_id|username")

        model = models.Player.from_db(player)

        return PangeaMessage(player=model)
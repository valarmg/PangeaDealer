import logging
from services import PangeaDbServiceBase
from utils.messages import PangeaMessage
from utils.errors import PangeaException, PangaeaDealerErrorCodes
import models

logger = logging.getLogger(__name__)


class LobbyService(PangeaDbServiceBase):
    def __init__(self, db):
        super().__init__(db)

    def create_lobby(self, name):
        logger.debug("create_lobby, name: {0}".format(name))

        if name is None or name.isspace():
            raise PangeaException.missing_field("name")

        lobby = {"name": name}
        self.db.lobby_create(lobby)

        model = models.Lobby()
        model.from_dict(lobby)

        return PangeaMessage(lobby=model)

    def get_lobbies(self):
        logger.debug("get_lobbies")
        documents = self.db.lobby_get_all()

        data = []
        for lobby in documents:
            data.append(models.Lobby.from_db(lobby))

        return PangeaMessage(lobbies=data)

    def get_lobby(self, lobby_id):
        logger.debug("get_lobby: {0}".format(lobby_id))

        lobby = self.db.lobby_get_by_id(lobby_id)

        return PangeaMessage(lobby=lobby)

    def delete_lobby(self, lobby_id):
        logger.debug("delete_lobby: {0}".format(lobby_id))

        self.db.lobby_delete(lobby_id)

    def delete_lobbies(self):
        logger.debug("delete_lobbies")

        self.db.lobby_delete_all()
import logging
from services import PangeaDbServiceBase
from utils.messages import PangeaMessage
from utils.errors import PangeaException, PangaeaDealerErrorCodes
import models


class LobbyService(PangeaDbServiceBase):
    log = logging.getLogger(__name__)

    def __init__(self, db):
        super().__init__(db)

    def create_lobby(self, name):
        self.log.debug("create_lobby, name: {0}".format(name))

        if name is None or name.isspace():
            raise PangeaException.missing_field("name")

        lobby = self.db.lobby_create(name)
        return PangeaMessage(lobby=lobby)

    def get_lobbies(self):
        self.log.debug("get_lobbies")

        lobbies = self.db.lobby_get_all()
        return PangeaMessage(lobbies=lobbies)

    def get_lobby(self, lobby_id):
        self.log.debug("get_lobby: {0}".format(lobby_id))

        lobby = self.db.lobby_get_by_id(lobby_id)

        return PangeaMessage(lobby=lobby)

    def delete_lobby(self, lobby_id):
        self.log.debug("delete_lobby: {0}".format(lobby_id))

        self.db.lobby_delete(lobby_id)

    def delete_lobbies(self):
        self.log.debug("delete_lobbies")

        self.db.lobby_delete_all()
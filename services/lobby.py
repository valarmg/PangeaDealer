import logging
from services import PangeaDbServiceBase
from utils.messages import PangeaMessage
from bson import json_util
from bson import BSON
import models

logger = logging.getLogger(__name__)


class LobbyService(PangeaDbServiceBase):
    def __init__(self, db, client_manager):
        super().__init__(db, client_manager)

    def create_lobby(self, name):
        logger.debug("create_lobby, name: {0}".format(name))

        lobby = {"name": name}
        self.db.lobby_create(lobby)
        self.fire_lobby_refresh()

        return lobby

    def get_lobbies(self, client):
        logger.debug("get_lobbies")
        documents = self.db.lobby_get_all()

        data = []
        for lobby in documents:
            data.append(models.Lobby.from_db(lobby))

        message = PangeaMessage(lobbies=data)

        client.send_message(message)

    def delete_lobby(self, lobby_id):
        logger.debug("delete_lobby: {0}".format(lobby_id))

        self.db.lobby_delete(lobby_id)

    def delete_lobbies(self):
        logger.debug("delete_lobbies")

        self.db.lobby_delete_all()

    def fire_lobby_refresh(self):
        lobbies = self.db.lobby_get_all()

        data = []
        for lobby in lobbies:
            data.append(models.Lobby.from_db(lobby))

        logger.debug(lobbies)
        logger.debug(data)

        message = PangeaMessage(lobbies=data)

        logger.debug("fire_lobby_refresh: {0}".format(message.to_json()))
        clients = self.client_manager.get_clients()

        for client in clients:
            client.send_message(message)
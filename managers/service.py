import logging
import traceback
from services.dealer import DealerService
from services.table import TableService
from services.lobby import LobbyService
from utils.messages import PangeaMessage
from utils.errors import PangaeaErrorCodes, PangeaException
from db import PangeaDb

logger = logging.getLogger(__name__)


class ServiceManager(object):
    def __init__(self, client_manager):
        logger.info("ServiceManager")

        self.client_manager = client_manager
        self.db = PangeaDb()

        self.dealer_service = DealerService(self.db, self.client_manager)
        self.table_service = TableService(self.db, self.client_manager)
        self.lobby_service = LobbyService(self.db, self.client_manager)

    def process_message(self, client, message: PangeaMessage):
        logger.info("process_message: {0}".format(message))

        # Each message type should have an associated method
        if message.message_type is None:
            raise PangeaException.missing_field("message_type")
        if not hasattr(self, message.message_type):
            raise PangeaException(PangaeaErrorCodes.InvalidArgument,
                                  "Unknown message type: '{0}'".format(message.message_type))

        method = getattr(self, message.message_type)

        try:
            method(client, message)
        except Exception as ex:
            logger.error("Got exception: {0}".format(traceback.format_exc()))
            msg = PangeaMessage.from_exception(message.message_type, ex)
            client.send_message(msg)

    # -- Lobby -- #
    def create_lobby(self, client, message):
        if message.name is None:
            raise PangeaException.missing_field("name")

        self.lobby_service.create_lobby(message.name)

    def get_lobbies(self, client, message):
        self.lobby_service.get_lobbies(client)

    def delete_lobby(self, client, message):
        if message.lobby_id is None:
            raise PangeaException.missing_field("lobby_id")

        self.lobby_service.delete_lobby(message.lobby_id)

    def clear_lobbies(self, client, message):
        self.lobby_service.delete_lobbies()

    # -- Table -- #
    def create_table(self, client, message):
        if message.lobby_id is None:
            raise PangeaException.missing_field("lobby_id")
        if message.name is None:
            raise PangeaException.missing_field("name")

        self.table_service.create_table(message.lobby_id, message.name)

    def join_table(self, client, message):
        self.table_service.join_table(message.table_id, message.player_id)

    def get_tables(self, client, message):
        if message.lobby_id is None:
            raise PangeaException.missing_field("lobby_id")

        self.table_service.get_tables(client, message.lobby_id)

    def get_table(self, client, message):
        if message.table_id is None:
            raise PangeaException.missing_field("table_id")

        self.table_service.get_table(client, message.table_id)
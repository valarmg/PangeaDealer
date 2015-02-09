import logging

from tornado.web import RequestHandler
from tornado.websocket import WebSocketHandler
from managers.service import ServiceManager
from utils.messages import PangeaMessage


class IndexHandler(RequestHandler):
    port = None

    def initialize(self, port):
        self.port = port

    def get(self):
        example_requests = [
            '{ "message_type": "create_lobby", "name": "test lobby" }',
            '{ "message_type": "create_table", "name": "test table", "lobby_id": ""}',
            '{ "message_type": "get_tables", "lobby_id": ""}',
            '{ "message_type": "join_table", "table_id": ""}',
        ]

        self.render("index.html", port=self.port, example_requests="\n".join(example_requests))


class WsHandler(WebSocketHandler):
    logger = logging.getLogger(__name__)

    request = None
    client_manager = None
    service_manager = None

    def initialize(self, client_manager):
        self.client_manager = client_manager
        self.service_manager = ServiceManager(client_manager)

    def get_player_id(self):
        return None if self.request is None else self.request.player_id

    def get_player_name(self):
        return None if self.request is None else self.request.player_name

    def get_table_id(self):
        return None if self.request is None else self.request.table_id

    def open(self):
        self.logger.debug("Opened websocket connection")
        self.client_manager.add_client(self)

    def on_close(self):
        self.logger.debug("Websocket connection closed")
        self.client_manager.remove_client(self)

    def on_message(self, message):
        self.logger.debug("Received message: {0}".format(message))
        parsed = PangeaMessage.from_json(message)
        self.service_manager.process_message(self, parsed)

    def on_error(self, message):
        self.logger.debug("Received error: {0}".format(message))

    def send_message(self, message: PangeaMessage):
        self.logger.debug("Sending message: {0}".format(message))
        self.write_message(message.to_json())
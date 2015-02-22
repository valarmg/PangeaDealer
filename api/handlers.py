import logging
import json
import urllib

from tornado.web import RequestHandler
from utils.messages import PangeaMessage
from db import PangeaDb
from services.table import TableService
from services.dealer import DealerService
from services.lobby import LobbyService


class IndexHandler(RequestHandler):
    def initialize(self):
        pass

    def get(self):
        self.render("index.html", port=self.application.port, routes=self.application.get_routes())


class ApiHandler(RequestHandler):
    logger = logging.getLogger(__name__)

    db = None
    dealer_service = None
    table_service = None
    lobby_service = None
    json_body = None

    def initialize(self):
        self.db = PangeaDb()
        self.dealer_service = DealerService(self.db)
        self.table_service = TableService(self.db)
        self.lobby_service = LobbyService(self.db)

    def prepare(self):
        if "Content-Type" in self.request.headers \
                and self.request.headers["Content-Type"].startswith("application/json")\
                and self.request.body is not None:

            # TODO: iso timestamp mapping?
            self.logger.info("Received request message: {0}".format(self.request.body))
            body = self.request.body.decode('utf-8')
            if body:
                self.json_body = json.loads(body)

    def get_json_body_argument(self, name, default=None):
        if self.json_body is None:
            return default
        return self.json_body.get(name, default)

    def send_pangea_response(self, response):
        message = response.to_json()
        self.logger.info("Sending response: {0}".format(message))

        self.set_header("Content-Type", "application/json")
        self.write(message)


class LobbyHandler(ApiHandler):
    def get(self, lobby_id=None):
        if lobby_id:
            response = self.lobby_service.get_lobby(lobby_id)
        else:
            response = self.lobby_service.get_lobbies()

        self.send_pangea_response(response)

    def post(self):
        name = self.get_json_body_argument("name")
        response = self.lobby_service.create_lobby(name)
        self.send_pangea_response(response)


class TableHandler(ApiHandler):

    def get(self, table_id=None):
        if table_id:
            response = self.table_service.get_table(table_id)
        else:
            lobby_id = self.get_query_argument("lobby_id", None, True)
            response = self.table_service.get_tables(lobby_id)

        self.send_pangea_response(response)

    def post(self):
        lobby_id = self.get_json_body_argument("lobby_id")
        name = self.get_json_body_argument("name")
        response = self.table_service.create_table(lobby_id, name)
        self.send_pangea_response(response)
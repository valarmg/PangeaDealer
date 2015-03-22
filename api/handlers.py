import logging
import json
import urllib
from email.utils import parsedate
from datetime import datetime

from tornado.web import RequestHandler
from utils.messages import PangeaMessage
from utils.errors import PangaeaDealerErrorCodes
from db import PangeaDb
from services.table import TableService
from services.dealer import DealerService
from services.lobby import LobbyService
from services.player import PlayerService
from services.bet import BetService


class IndexHandler(RequestHandler):
    def initialize(self):
        pass

    def get(self):
        self.render("index.html", host_name=self.application.host_name, port=self.application.port, routes=self.application.get_routes())


class ApiHandler(RequestHandler):
    logger = logging.getLogger(__name__)

    db = None
    dealer_service = None
    table_service = None
    lobby_service = None
    player_service = None
    bet_service = None
    json_body = None

    def initialize(self):
        self.db = PangeaDb()
        self.dealer_service = DealerService(self.db)
        self.table_service = TableService(self.db)
        self.lobby_service = LobbyService(self.db)
        self.player_service = PlayerService(self.db)
        self.bet_service = BetService(self.db)

    def prepare(self):
        if "Content-Type" in self.request.headers \
                and self.request.headers["Content-Type"].startswith("application/json")\
                and self.request.body is not None:

            # TODO: iso timestamp mapping?
            self.logger.info("Received request message: {0}".format(self.request.body))
            body = self.request.body.decode('utf-8')
            if body:
                self.json_body = json.loads(body)

    def write_error(self, status_code, **kwargs):
        if "exc_info" in kwargs:
            response = PangeaMessage().from_exception("", kwargs["exc_info"][1])
            self.send_pangea_response(response)
        else:
            super().write_error(status_code, kwargs)

    def get_json_body_argument(self, name, default=None):
        if self.json_body is None:
            return default
        return self.json_body.get(name, default)

    def send_pangea_response(self, response):
        message = response.to_json()
        self.logger.info("Sending response: {0}".format(message))

        self.set_header("Content-Type", "application/json")
        self.write(message)

    def if_modified_since(self):
        header = self.request.headers.get("If-Modified-Since")
        if header:
            email_date = parsedate(header)
            return datetime(*email_date[:6])
        return None


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


class TableStatusHandler(ApiHandler):

    def get(self, table_id):
        player_id = self.get_query_argument("player_id", None, True)
        response = self.table_service.get_table_status(table_id, player_id, self.if_modified_since())

        self.send_pangea_response(response)


class PlayerHandler(ApiHandler):

    def get(self, player_id):
        if player_id:
            response = self.player_service.get_player(player_id)
        else:
            response = self.player_service.get_players()

        self.send_pangea_response(response)

    def post(self):
        name = self.get_json_body_argument("username")
        response = self.player_service.create_player(name)
        self.send_pangea_response(response)


class SeatsHandler(ApiHandler):

    def post(self):
        table_id = self.get_json_body_argument("table_id")
        player_id = self.get_json_body_argument("player_id")
        seat_number = self.get_json_body_argument("seat_number")
        stack = self.get_json_body_argument("stack")

        response = self.table_service.join_table(table_id, player_id, seat_number, stack)
        self.send_pangea_response(response)

    def delete(self,):
        table_id = self.get_query_argument("table_id")
        player_id = self.get_query_argument("player_id")

        response = self.table_service.leave_table(table_id, player_id)
        self.send_pangea_response(response)


class BetHandler(ApiHandler):

    def post(self):
        table_id = self.get_json_body_argument("table_id")
        player_id = self.get_json_body_argument("player_id")
        amount = self.get_json_body_argument("amount")

        response = self.table_service.bet(table_id, player_id, amount)
        self.send_pangea_response(response)
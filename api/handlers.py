import logging
import json
import time
from email.utils import parsedate
from datetime import datetime

from tornado.web import RequestHandler
from utils.messages import PangeaMessage
from services.table import TableService
from services.lobby import LobbyService
from services.player import PlayerService
from services.bet import BetService
from services.chat import ChatService
from db import PangeaDb


class IndexHandler(RequestHandler):
    def initialize(self):
        pass

    def get(self):
        if self.application.port == 8080:
            base_url = "http://{0}".format(self.application.host_name)
        else:
            base_url = "http://{0}:{1}".format(self.application.host_name, self.application.port)

        self.render("index.html", base_url=base_url, routes=self.application.get_routes())


class ApiHandler(RequestHandler):
    logger = logging.getLogger(__name__)

    db = None
    table_service = None
    lobby_service = None
    player_service = None
    bet_service = None
    chat_service = None
    json_body = None

    def initialize(self):
        self.db = PangeaDb()
        self.table_service = TableService(self.db)
        self.lobby_service = LobbyService(self.db)
        self.player_service = PlayerService(self.db)
        self.bet_service = BetService(self.db)
        self.chat_service = ChatService(self.db)

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
            date_tuple = parsedate(header)
            return datetime.fromtimestamp(time.mktime(date_tuple))
            #email_date = parsedate(header)
            #return datetime(*email_date[:6])
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

    def delete(self,):
        lobby_id = self.get_query_argument("lobby_id", None)

        response = self.lobby_service.delete_lobby(lobby_id)
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
        use_default = self.get_json_body_argument("use_default", False)

        response = self.table_service.create_table(lobby_id, name, use_default)
        self.send_pangea_response(response)

    def delete(self,):
        table_id = self.get_query_argument("table_id", None)

        response = self.table_service.delete_table(table_id)
        self.send_pangea_response(response)


class TableStatusHandler(ApiHandler):

    def get(self, table_id):
        player_id = self.get_query_argument("player_id", None, True)
        response = self.table_service.get_table_status(table_id, player_id, self.if_modified_since())

        self.send_pangea_response(response)


class PlayerHandler(ApiHandler):

    def get(self, player_id=None, ):
        if player_id:
            response = self.player_service.get_player(player_id)
        else:
            table_id = self.get_query_argument("table_id", None, True)
            response = self.player_service.get_players(table_id)

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
        check = self.get_json_body_argument("check")
        fold = self.get_json_body_argument("fold")

        if check:
            response = self.bet_service.check(table_id, player_id)
        elif fold:
            response = self.bet_service.fold(table_id, player_id)
        else:
            response = self.bet_service.bet(table_id, player_id, amount)

        self.send_pangea_response(response)


class ChatHandler(ApiHandler):

    def post(self):
        table_id = self.get_json_body_argument("table_id")
        player_id = self.get_json_body_argument("player_id")
        chat_message = self.get_json_body_argument("chat_message")

        response = self.chat_service.chat(table_id, player_id, chat_message)
        self.send_pangea_response(response)
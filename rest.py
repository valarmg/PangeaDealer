import os
import logging
from tornado.options import parse_command_line
from tornado.ioloop import IOLoop
from tornado.web import Application, StaticFileHandler
from tornado.httpserver import HTTPServer
from api.handlers import *


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class PangeaApp(Application):

    def __init__(self, port):
        self.port = port
        object_id_regex = "[0-9a-fA-F]{24}"

        handlers = [
            (r"/", IndexHandler),
            (r"/css/(.*)", StaticFileHandler, {"path": "./static/css"}),
            (r"/js/(.*)", StaticFileHandler, {"path": "./static/js"}),
            (r"/api/lobbies/({0})".format(object_id_regex), LobbyHandler),
            (r"/api/lobbies$", LobbyHandler),
            (r"/api/tables/({0})".format(object_id_regex), TableHandler),
            (r"/api/tables/status/({0})".format(object_id_regex), TableStatusHandler),
            (r"/api/tables$", TableHandler),
            (r"/api/players$", PlayerHandler),
            (r"/api/players/({0})".format(object_id_regex), PlayerHandler),
            (r"/api/seats$", SeatsHandler),
            (r"/api/bets$", BetHandler)
        ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            #debug=True
        )
        Application.__init__(self, handlers, **settings)

    def get_routes(self):
        return [handler.regex.pattern for handler in self.handlers[0][1] if handler.regex.pattern.startswith("/api")]

if __name__ == "__main__":
    server_port = 10006
    application = PangeaApp(server_port)
    server = HTTPServer(application)

    logger.debug("Running server on http://localhost:{0}".format(server_port))

    server.listen(server_port)
    IOLoop.instance().start()

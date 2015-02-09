import os
import logging

from tornado.options import parse_command_line
from tornado.ioloop import IOLoop
from tornado.web import Application, StaticFileHandler
from tornado.httpserver import HTTPServer

from server.handler import IndexHandler, WsHandler
from managers.client import ClientManager


#define("port", default=8888, help="Run on the given port", type=int)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class PangeaApplication(Application):
    def __init__(self, port):
        client_manager = ClientManager()

        handlers = [
            (r"/", IndexHandler, dict(port=port)),
            (r"/websocket", WsHandler, dict(client_manager=client_manager)),
            (r"/css/(.*)", StaticFileHandler, {"path": "./static/css"}),
            (r"/js/(.*)", StaticFileHandler, {"path": "./static/js"}),
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
        )
        Application.__init__(self, handlers, **settings)

if __name__ == '__main__':
    wsport = 10004

    logger.info("http://localhost:{0}/".format(wsport))
    logger.info("Listening with web sockets on port {0}".format(wsport))

    #parse_command_line()
    application = PangeaApplication(wsport)
    server = HTTPServer(application)

    server.listen(wsport)
    IOLoop.instance().start()

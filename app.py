import os
import logging
from tornado.options import parse_command_line
from tornado.ioloop import IOLoop
from tornado.wsgi import WSGIApplication
from tornado.web import StaticFileHandler
from tornado.httpserver import HTTPServer
from api.handlers import *


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class PangeaApp(WSGIApplication):

    def __init__(self, port, host_name):
        self.port = port
        self.host_name = host_name
        object_id_regex = "[0-9a-fA-F]{24}"

        # if "OPENSHIFT_REPO_DIR" in os.environ:
        #     static_path = os.path.join(os.environ['OPENSHIFT_REPO_DIR'], "static")
        #     template_path = os.path.join(os.environ['OPENSHIFT_REPO_DIR'], "templates")
        # else:
        #     static_path = os.path.join(os.path.dirname(__file__), "static")
        #     template_path = os.path.join(os.path.dirname(__file__), "templates")

        static_path = os.path.join(os.path.dirname(__file__), "static")
        template_path = os.path.join(os.path.dirname(__file__), "templates")

        for item in os.environ:
            logger.debug("{0}={1}".format(item, os.environ[item]))

        logger.debug("static_path: " + static_path)
        logger.debug("template_path: " + template_path)

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
            template_path=template_path,
            static_path=static_path,
            #debug=True
        )
        WSGIApplication.__init__(self, handlers, **settings)

    def get_routes(self):
        return [handler.regex.pattern for handler in self.handlers[0][1] if handler.regex.pattern.startswith("/api")]


def setup_virtual_environment():
    if "OPENSHIFT_PYTHON_DIR" in os.environ:
        virtenv = os.environ["OPENSHIFT_PYTHON_DIR"] + "/virtuenv/"
        virtualenv = os.path.join(virtenv, 'bin/activate_this.py')

        try:
            exec_namespace = dict(__file__=virtualenv)
            with open(virtualenv, 'rb') as exec_file:
                file_contents = exec_file.read()
            compiled_code = compile(file_contents, virtualenv, 'exec')
            exec(compiled_code, exec_namespace)
        except IOError:
            pass

setup_virtual_environment()

server_ip = os.environ["OPENSHIFT_PYTHON_IP"] if "OPENSHIFT_PYTHON_IP" in os.environ else "localhost"
server_port = int(os.environ["OPENSHIFT_PYTHON_PORT"]) if "OPENSHIFT_PYTHON_PORT" in os.environ else 10006
server_name = os.environ["OPENSHIFT_GEAR_DNS"] if "OPENSHIFT_GEAR_DNS" in os.environ else "localhost"

application = PangeaApp(server_port, server_name)
server = HTTPServer(application)

logger.debug("Running server on http://{0}:{1}".format(server_name, server_port))

server.listen(server_port, server_ip)
IOLoop.instance().start()

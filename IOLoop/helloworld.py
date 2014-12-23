import tornado.ioloop
import tornado.web

# http://www.tornadoweb.org/en/stable/options.html
from tornado.options import parse_command_line, define, options

define("port", default=8888)
define("debug", default=False)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        name = self.get_argument("name", default="world")

        self.write("Hello, {}!".format(name))

handlers = [
    (r"/", MainHandler),
]

if __name__ == "__main__":
    parse_command_line()

    application = tornado.web.Application(handlers, debug=options.debug)
    application.listen(options.port)

    tornado.ioloop.IOLoop.instance().start()

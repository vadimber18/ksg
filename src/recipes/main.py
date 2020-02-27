import logging
import sys

import aiohttp_jinja2
import jinja2
from aiohttp import web

from .db import close_pg, init_pg
from .middlewares import setup_middlewares
from .routes import setup_routes, setup_cors
from .settings import CONFIG, TEST_CONFIG
from .admin import setup_admin
from .helpers import shutdown_ws, init_logstash, init_redis


async def init_app(testing=False):
    app = web.Application()

    app['websockets'] = {}  # TODO do we actually need em?

    app['config'] = TEST_CONFIG if testing else CONFIG
    app['testing'] = True if testing else False

    # setup Jinja2 template renderer
    aiohttp_jinja2.setup(
        app, loader=jinja2.PackageLoader('recipes', 'templates'))

    # create db connection on startup, shutdown on exit
    # app.on_startup.append(init_pg)
    pg = await init_pg(app)
    setup_admin(app, pg)

    app.on_cleanup.append(close_pg)
    app.on_cleanup.append(shutdown_ws)

    if not testing:
        app.cleanup_ctx.append(init_logstash)
        app.cleanup_ctx.append(init_redis)

    # setup views and routes
    setup_routes(app)
    # setup cors for swagger
    setup_cors(app)

    setup_middlewares(app)

    return app


def main(argv):
    logging.basicConfig(level=logging.DEBUG)

    app = init_app(argv)

    config = CONFIG
    web.run_app(app,
                host=config['host'],
                port=config['port'])


if __name__ == '__main__':
    main(sys.argv[1:])

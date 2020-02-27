import aiohttp
import aiohttp_jinja2
from aiohttp import web

from scrape import collect_recipes

from . import db
from .utils import get_random_name


# non-api handlers (do we need?)
@aiohttp_jinja2.template('recipes.html')
async def recipes_nonapi(request):
    try:
        recipes, count = await db.get_recipe_list(request.app['db'], pagination={'limit': 300}, filters=None)
        return {'recipes': recipes, 'count': count}
    except Exception:
        return {'recipes': None, 'count': None}


async def recipe_detail_nonapi(request):
    recipe_id = request.match_info['recipe_id']

    ws_current = web.WebSocketResponse()
    ws_ready = ws_current.can_prepare(request)
    if not ws_ready.ok:
        try:
            recipe = await db.get_recipe_list(request.app['db'],
                                              filters=recipe_id,
                                              many=False)
            return aiohttp_jinja2.render_template('recipe_detail.html', request, {'recipe': recipe})
        except Exception:
            return aiohttp_jinja2.render_template('recipe_detail.html', request, {'recipe': None})

    await ws_current.prepare(request)

    name = get_random_name()

    await ws_current.send_json({'action': 'connect', 'name': name})

    for ws in request.app['websockets'].values():
        await ws.send_json({'action': 'join', 'name': name})
    request.app['websockets'][name] = ws_current

    while True:
        msg = await ws_current.receive()

        if msg.type == aiohttp.WSMsgType.text:
            for ws in request.app['websockets'].values():
                if ws is not ws_current:
                    await ws.send_json(
                        {'action': 'sent', 'name': name, 'text': msg.data})
        else:
            break

    del request.app['websockets'][name]
    for ws in request.app['websockets'].values():
        await ws.send_json({'action': 'disconnect', 'name': name})

    return ws_current


@aiohttp_jinja2.template('collect.html')
async def collect_nonapi(request):
    await collect_recipes(request)
    return {}

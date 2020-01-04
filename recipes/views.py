import aiohttp
import aiohttp_jinja2
from aiohttp import web

from scrape import collect_recipes

from . import db
from .helpers import prepare_filter_parameters, prepare_recipes_response
from .utils import json_str_dumps, get_random_name
from .middlewares import login_required # TODO need another location


async def register(request):
    data = await request.json()
    try:
        await db.register(request.app['db'], data)
    except Exception as e:
        return web.json_response(str(e), status=web.HTTPBadRequest.status_code)
    return web.Response(status=web.HTTPCreated.status_code)


async def login(request):
    data = await request.json()
    try:
        token = await db.login(request.app['db'], data, request.app['config']['jwt'])
    except Exception as e:
        return web.json_response(str(e), status=web.HTTPBadRequest.status_code)

    return web.json_response({'token': token.decode('utf-8')})


async def recipes(request):
    try:
        pagination, filters = prepare_filter_parameters(request.query)
        recipes, count = await db.get_recipe_list(request.app['db'], pagination, filters, request.user)
        response = prepare_recipes_response(recipes, count, request.rel_url)
        return web.json_response(response, dumps=json_str_dumps)
    except Exception as e:
        return web.Response(body=str(e), status=web.HTTPBadRequest.status_code)


@login_required
async def favored(request):
    try:
        pagination, filters = prepare_filter_parameters(request.query)
        recipes, count = await db.get_recipe_list(request.app['db'], pagination, filters, request.user, favored=True)
        response = prepare_recipes_response(recipes, count, request.rel_url)
        return web.json_response(response, dumps=json_str_dumps)
    except Exception as e:
        return web.Response(body=str(e), status=web.HTTPBadRequest.status_code)


async def recipe_detail(request):
    ''' detail view '''
    recipe_id = request.match_info['recipe_id']
    try:
        recipe = await db.get_recipe_list(request.app['db'],
                                          filters=recipe_id,
                                          usr=request.user,
                                          many=False)
        return web.json_response(recipe, dumps=json_str_dumps)
    except Exception as e:
        return web.Response(body=str(e), status=web.HTTPBadRequest.status_code)


@login_required
async def vote_recipe(request):
    ''' detail view '''
    recipe_id = request.match_info['recipe_id']
    try:
        await db.vote_recipe(request.app['db'], recipe_id, request.user)
        return web.json_response({'success': True})
    except Exception as e:
        return web.Response(body=str(e), status=web.HTTPBadRequest.status_code)


@login_required
async def comment_recipe(request):
    ''' detail view '''
    data = await request.json()
    recipe_id = request.match_info['recipe_id']
    try:
        await db.comment_recipe(request.app['db'], data, recipe_id, request.user)
        return web.json_response({'success': True})
    except Exception as e:
        return web.Response(body=str(e), status=web.HTTPBadRequest.status_code)


@aiohttp_jinja2.template('recipes.html')
async def recipes_nonapi(request):
    try:
        recipes, count = await db.get_recipe_list(request.app['db'], pagination={'limit':300}, filters=None)
        return {'recipes': recipes, 'count': count}
    except Exception as e:
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
        except Exception as e:
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
async def collect(request):
    await collect_recipes(request)
    return {}

import os

from aiohttp import web

from scrape import collect_recipes

from . import db
from .utils import json_str_dumps
from .exceptions import BadRequest_Important, AppException
from .helpers import prepare_filter_parameters, prepare_recipes_response, log_string, log_exception, \
    generate_userpic_filename, run_sync
from .middlewares import login_required # TODO find another location


async def register(request):
    data = await request.json()
    try:
        await db.register(request.app['db'], data)
        log_string(request.app, 'new registration!', extra={'username': data['username']})
        return web.Response(status=web.HTTPCreated.status_code)
    except AppException as e:
        return web.json_response(str(e), status=web.HTTPBadRequest.status_code)
    except Exception as e:
        log_exception(request.app, e)
        return web.json_response(str(e), status=web.HTTPBadRequest.status_code)


async def login(request):
    data = await request.json()
    try:
        token = await db.login(request.app['db'], data, request.app['config']['jwt'])
        log_string(request.app, 'new auth!', extra={'username': data['username']})
        return web.json_response({'token': token.decode('utf-8')})
    except AppException as e:
        return web.json_response(str(e), status=web.HTTPBadRequest.status_code)
    except BadRequest_Important as e:
        log_string(request.app, f'auth attempt: {e}', extra={'username': data['username']})
        return web.json_response(str(e), status=web.HTTPBadRequest.status_code)
    except Exception as e:
        log_exception(request.app, e)
        return web.json_response(str(e), status=web.HTTPBadRequest.status_code)


async def recipes(request):
    try:
        pagination, filters = prepare_filter_parameters(request.query)
        recipes, count = await db.get_recipe_list(request.app['db'], pagination, filters, request.user)
        response = prepare_recipes_response(recipes, count, request.rel_url)
        return web.json_response(response, dumps=json_str_dumps)
    except AppException as e:
        return web.json_response(str(e), status=web.HTTPBadRequest.status_code)
    except Exception as e:
        log_exception(request.app, e)
        return web.Response(body=str(e), status=web.HTTPBadRequest.status_code)


@login_required
async def favored(request):
    try:
        pagination, filters = prepare_filter_parameters(request.query)
        recipes, count = await db.get_recipe_list(request.app['db'], pagination, filters, request.user, favored=True)
        response = prepare_recipes_response(recipes, count, request.rel_url)
        return web.json_response(response, dumps=json_str_dumps)
    except AppException as e:
        return web.json_response(str(e), status=web.HTTPBadRequest.status_code)
    except Exception as e:
        log_exception(request.app, e)
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
    except AppException as e:
        return web.json_response(str(e), status=web.HTTPBadRequest.status_code)
    except Exception as e:
        log_exception(request.app, e)
        return web.Response(body=str(e), status=web.HTTPBadRequest.status_code)


@login_required
async def vote_recipe(request):
    ''' detail view '''
    recipe_id = request.match_info['recipe_id']
    try:
        await db.vote_recipe(request.app['db'], recipe_id, request.user)
        return web.Response(status=web.HTTPCreated.status_code)
    except AppException as e:
        return web.json_response(str(e), status=web.HTTPBadRequest.status_code)
    except Exception as e:
        log_exception(request.app, e)
        return web.Response(body=str(e), status=web.HTTPBadRequest.status_code)


@login_required
async def comment_recipe(request):
    ''' detail view '''
    data = await request.json()
    recipe_id = request.match_info['recipe_id']
    try:
        await db.comment_recipe(request.app['db'], data, recipe_id, request.user)
        log_string(request.app, 'new comment!', extra={'user': request.user['id'],
                                                       'recipe': recipe_id,
                                                       'body': data['body']})
        return web.Response(status=web.HTTPCreated.status_code)
    except AppException as e:
        return web.json_response(str(e), status=web.HTTPBadRequest.status_code)
    except Exception as e:
        log_exception(request.app, e)
        return web.Response(body=str(e), status=web.HTTPBadRequest.status_code)


@login_required
async def collect(request):
    ''' collect API handler '''
    if not request.user.get('superuser'):
        recently_collected = await request.app['redis'].exists('collected')
        if recently_collected:
            ttl = await request.app['redis'].ttl('collected')
            log_string(request.app, 'collect request denied', extra={'user': request.user['id'], 'ttl': ttl})
            return web.json_response({'message':'Collection cannot be performed', 'ttl': ttl},
                                     status=web.HTTPForbidden.status_code)
    log_string(request.app, 'collect successful request', extra={'user': request.user['id']})
    await collect_recipes(request)
    await request.app['redis'].set('collected', 'placeholder', expire = 60 * 60 * 6)  # 6 hours
    return web.Response()


@login_required
async def userpic_upload(request):
    try:
        reader = await request.multipart()

        field = await reader.next()
        assert field.name == 'file'
        request_filename = field.filename
        path = request.app['config']['upload_path']

        with open(os.path.join(path, request_filename), 'wb') as f:
            while True:
                chunk = await field.read_chunk()  # 8192 bytes by default.
                if not chunk:
                    break
                f.write(chunk)

        filename = await run_sync(generate_userpic_filename, request.user, request_filename, path)
        user = await db.set_userpic(request.app['db'], filename, request.user)

        log_string(request.app, f'uploaded userpic', extra={'user': user['id']})
        return web.json_response(user, dumps=json_str_dumps)

    except BadRequest_Important as e:
        log_string(request.app, f'userpic upload denied: {e}', extra={'user': request.user['id'],
                                                                      'request_filename': request_filename})
        return web.json_response(str(e), status=web.HTTPBadRequest.status_code)
    except Exception as e:
        return web.json_response(str(e), status=web.HTTPBadRequest.status_code)


@login_required
async def current_user(request):
    ''' returns current logged user model '''
    try:
        user = await db.user_by_id(request.app['db'], request.user['id'])
        return web.json_response(user)
    except Exception as e:
        return web.Response(body=str(e), status=web.HTTPBadRequest.status_code)

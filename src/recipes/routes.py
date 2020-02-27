import pathlib

from .views import collect_nonapi, recipes_nonapi, recipe_detail_nonapi
from .api import register, login, recipes, favored, recipe_detail, vote_recipe, comment_recipe, collect, \
    current_user, userpic_upload

import aiohttp_cors

PROJECT_ROOT = pathlib.Path(__file__).parent


def setup_routes(app):
    # api endpoints
    app.router.add_route('POST', '/api/register', register)
    app.router.add_route('POST', '/api/login', login)

    app.router.add_route('GET', '/api/users/current', current_user)
    app.router.add_route('POST', '/api/users/set_pic', userpic_upload)

    app.router.add_route('GET', '/api/recipes', recipes)
    app.router.add_route('GET', '/api/recipes/favored', favored)
    app.router.add_route('GET', '/api/recipes/{recipe_id}', recipe_detail)
    app.router.add_route('POST', '/api/recipes/{recipe_id}/vote', vote_recipe)
    app.router.add_route('POST', '/api/recipes/{recipe_id}/comment', comment_recipe)
    app.router.add_route('POST', '/api/recipes/collect', collect)

    # some basic views for collection and list of recipes view
    app.router.add_get('/collect', collect_nonapi, name='collect')
    app.router.add_get('/recipes', recipes_nonapi, name='recipes_nonapi')
    app.router.add_get('/recipes/{recipe_id}', recipe_detail_nonapi, name='recipe_detail_nonapi')
    # app.router.add_get('/', recipe_detail_nonapi, name='recipe_detail_nonapi')

    if app['config']['debug']:
        setup_static_routes(app)


def setup_cors(app):
    SWAGGER_PORT = 8001 if app['config']['debug'] else 8000
    # swagger server
    cors = aiohttp_cors.setup(app, defaults={
        f"http://127.0.0.1:{SWAGGER_PORT}": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })

    for route in list(app.router.routes()):
        cors.add(route)


def setup_static_routes(app):
    app.router.add_static('/static/',
                          path=f'{PROJECT_ROOT}/static',
                          name='static')

    app.router.add_static('/uploads/',
                          path=app['config']['upload_path'],
                          name='uploads')

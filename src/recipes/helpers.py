from datetime import datetime, timedelta
import os
import logging
import asyncio
import imghdr

import aioredis
from aiologstash import create_tcp_handler

from .db_tables import recipe
from .exceptions import BadRequest_Important


async def shutdown_ws(app):
    for ws in app['websockets'].values():
        await ws.close()
    app['websockets'].clear()


def prepare_filter_parameters(query):
    # validating and combining filters w pagination
    filters = {}
    category = query.get('category')
    if category:
        assert [int(i) for i in category.split(',')]
        filters.update({'category': category})
    prep_time = query.get('prep_time')
    if prep_time:
        assert int(prep_time) > 0
        filters.update({'prep_time': prep_time})
    date_filter = {}
    _from = query.get('from')
    if _from:
        assert datetime.strptime(_from, '%d-%m-%Y')
        date_filter.update({'from': _from})
        filters.update({'date': date_filter})
    to = query.get('to')
    if to:
        assert datetime.strptime(to, '%d-%m-%Y')
        date_filter.update({'to': to})
        filters.update({'date': date_filter})

    pagination = {}
    limit = query.get('limit')
    if limit:
        assert int(limit) > 0
        pagination.update({'limit': limit})
    offset = query.get('offset')
    if offset:
        assert int(offset) > 0
        pagination.update({'offset': offset})
    return pagination, filters


def prepare_recipes_response(recipes, count, rel_url):
    # creates DRF-like paginated response
    if not len(rel_url.query_string):
        next_request = str(rel_url) + '?offset=20'
    else:
        offset = rel_url.query.get('offset')
        if not offset:
            next_request = str(rel_url) + '&offset=20'
        else:
            next_request = str(rel_url).replace(f'offset={offset}', f'offset={int(offset)+ 20}')

    return {'count': count, 'next': next_request,'results': recipes}


def make_where_list_recipes(filters, many=True):
    where_list = []

    if not filters:
        return where_list
    elif not many:
        # detail view w id or slug
        if filters.isdigit(): # recipe_id
            where_list.append(recipe.c.id==filters) # we pass recipe_id through
        else:
            where_list.append(recipe.c.slug==filters)
        return where_list
    else:
        category = filters.get('category')
        if category:
            where_list.append(recipe.c.category_id.in_([int(cat) for cat in category.split(',')]))
        prep_time = filters.get('prep_time')
        if prep_time:
            interval = timedelta(minutes=int(prep_time))
            where_list.append(recipe.c.prep_time <= interval)
        date = filters.get('date')
        if date:
            _from = date.get('from')
            if _from:
                from_date = datetime.strptime(_from, '%d-%m-%Y')
                where_list.append(recipe.c.pub_date >= from_date)
            to = date.get('to')
            if to:
                to_date = datetime.strptime(to, '%d-%m-%Y')
                where_list.append(recipe.c.pub_date <= to_date)
        return where_list


async def init_logstash(app):
    conf = app['config']['logstash']
    log_handler = None
    logger = logging.getLogger('ksg')
    logger.setLevel(logging.INFO)
    # check if elk container is up - then wait logstash to start
    elk_up = True if os.system(f'ping -c 1 {conf["server"]}') is 0 else False
    if elk_up:
        await asyncio.sleep(60)  # wait elk container started
    try:
        log_handler = await create_tcp_handler(conf['server'], conf['port'])
    except Exception as e:
        print(f'Cant connect to logstash: {e}')
    else:
        logger.addHandler(log_handler)
    app['logstash'] = logger

    yield

    if log_handler:
        log_handler.close()


def log_exception(app, e):
    log_string(app, f'Exception: {str(e)}')


def log_string(app, string, extra=None):
    if not app.get('logstash'):  # no elk w local config
        return
    testing = app.get('testing')
    if not testing:
        app['logstash'].info(string, extra=extra)


async def init_redis(app):
    conf = app['config']['redis']
    pool = await aioredis.create_redis_pool(address=f'redis://{conf["server"]}:{conf["port"]}',
                                            minsize=10,
                                            maxsize=20,
                                            timeout=10)
    app['redis'] = pool
    yield
    pool.close()
    await pool.wait_closed()


async def run_sync(blocking_io, *args):
    loop = asyncio._get_running_loop()
    return await loop.run_in_executor(None, blocking_io, *args)


def generate_userpic_filename(user, filename, path):
    fullname = os.path.join(path, filename)
    ext = imghdr.what(fullname)
    if not ext:
        os.remove(fullname)
        raise BadRequest_Important('Uploaded file is not an image')
    new_fullname = os.path.join(path, f'{user["id"]}.{ext}')
    os.rename(fullname, new_fullname )
    return new_fullname

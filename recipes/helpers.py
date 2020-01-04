from datetime import datetime, timedelta

from .db_tables import recipe


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
            where_list.append(recipe.c.category_id.in_([int(cat) for cat in category.split()]))
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

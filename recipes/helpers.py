from datetime import datetime, timedelta

from .db_tables import recipe


async def shutdown_ws(app):
    for ws in app['websockets'].values():
        await ws.close()
    app['websockets'].clear()


def prepare_filter_parameters(query):
    filters = {}
    if 'category' in query:
        assert [int(i) for i in query['category'].split(',')]
        filters.update({'category': query['category']})
    if 'prep_time' in query:
        assert int(query['prep_time']) > 0
        filters.update({'prep_time': query['prep_time']})
    date_filter = {}
    if 'from' in query:
        assert datetime.strptime(query['from'], '%d-%m-%Y')
        date_filter.update({'from': query['from']})
        filters.update({'date': date_filter})
    if 'to' in query:
        assert datetime.strptime(query['to'], '%d-%m-%Y')
        date_filter.update({'to': query['to']})
        filters.update({'date': date_filter})
    pagination = {}
    if 'limit' in query:
        assert int(query['limit']) > 0
        pagination.update({'limit': query['limit']})
    if 'offset' in query:
        assert int(query['offset']) > 0
        pagination.update({'offset': query['offset']})
    return pagination, filters


def prepare_recipes_response(recipes, count, rel_url):
    if not len(rel_url.query_string):
        next_request = str(rel_url) + '?offset=20'
    else:
        if not 'offset' in rel_url.query:
            next_request = str(rel_url) + '&offset=20'
        else:
            value = int(rel_url.query['offset'])
            next_request = str(rel_url).replace(f'offset={str(value)}', f'offset={str(value + 20)}')

    return {'count': count, 'next': next_request,'results': recipes}


def make_where_list_recipes(filters, many=True):
    where_list = []
    if not filters:
        return where_list
    if not many:
        if filters.isdigit(): # recipe_id
            where_list.append(recipe.c.id==filters) # we pass recipe_id through
        else:
            where_list.append(recipe.c.slug==filters)
        return where_list
    if 'category' in filters:
        where_list.append(recipe.c.category_id.in_([int(cat) for cat in filters['category'].split()]))
    if 'prep_time' in filters:
        interval = timedelta(minutes=int(filters['prep_time']))
        where_list.append(recipe.c.prep_time <= interval)
    if 'date' in filters:
        if 'from' in filters['date']:
            from_date = datetime.strptime(filters['date']['from'], '%d-%m-%Y')
            where_list.append(recipe.c.pub_date >= from_date)
        if 'to' in filters['date']:
            to_date = datetime.strptime(filters['date']['to'], '%d-%m-%Y')
            where_list.append(recipe.c.pub_date <= to_date)
    return where_list
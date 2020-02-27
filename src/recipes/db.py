from datetime import datetime, timedelta

import aiopg.sa

import jwt
import sqlalchemy as sa
from passlib.hash import sha256_crypt

from .helpers import make_where_list_recipes
from .exceptions import RecordNotFound
from .validators import validate_comment, validate_recipe, validate_login, validate_register
from .db_tables import (
    users, source, category, ingredient, ingredient_item,
    recipe, comment, vote
)


async def init_pg(app):
    conf = app['config']['postgres']
    engine = await aiopg.sa.create_engine(
        database=conf['database'],
        user=conf['user'],
        password=conf['password'],
        host=conf['host'],
        port=conf['port'],
        minsize=conf['minsize'],
        maxsize=conf['maxsize'],
    )
    app['db'] = engine
    return engine


async def close_pg(app):
    app['db'].close()
    await app['db'].wait_closed()


async def get_recipe_list(dbengine, pagination=None, filters=None, usr=None, many=True, favored=False):
    if pagination:
        limit = pagination['limit'] if 'limit' in pagination else 20
        offset = pagination['offset'] if 'offset' in pagination else 0
    else:
        limit, offset = 20, 0
    where_list = make_where_list_recipes(filters, many)

    async with dbengine.acquire() as conn:
        recipes = await get_pure_recipe_list(conn, limit, offset, where_list, usr, many, favored)
        # fetch related ingredient item list for recipes
        recipes = await fetch_ingredients_for_recipes(conn,recipes)
        # fetch related comment list for recipes
        recipes = await fetch_comments_for_recipes(conn, recipes)
        if many:
            # fetch count for full filtered recipe list
            count = await get_recipe_list_count(conn, where_list, favored, usr)
            return recipes, count
        return recipes[0]


async def fetch_comments_for_recipes(conn, recipes):
    comments = await get_pure_comment_list(conn, recipes)
    for _recipe in recipes:
        comment_list = []
        for _comment in comments:
            if _comment['recipe_id'] == _recipe['recipe_id']:
                comment_list.append(_comment)
        _recipe.update({'comments': comment_list})
    return recipes


async def get_pure_comment_list(conn, recipes):
    recipe_ids = [recipe['recipe_id'] for recipe in recipes]
    query = sa.select([comment.c.recipe_id, comment.c.body, comment.c.pub_date, users.c.username]).\
        select_from(
        comment.join(users, users.c.id == comment.c.user_id)
    ).where(comment.c.recipe_id.in_(recipe_ids))
    cursor = await conn.execute(query)
    comment_records = await cursor.fetchall()
    comments = [dict(q) for q in comment_records]
    return comments


async def fetch_ingredients_for_recipes(conn, recipes):
    ''' selects related ingredient for ingredient_item '''
    ingredient_items = await get_pure_ingredient_items_list(conn, recipes)
    # adding ingredient_items to recipes
    for _recipe in recipes:
        ingredient_item_list = []
        for _ingredient_item in ingredient_items:
            if _ingredient_item['recipe_id'] == _recipe['recipe_id']:
                ingredient_item_list.append(_ingredient_item)
        _recipe.update({'ingredients': ingredient_item_list})
    return recipes


async def get_pure_ingredient_items_list(conn, recipes):
    if recipes:
        recipe_ids = str(tuple(recipe['recipe_id'] for recipe in recipes)).replace(',)', ')')
        raw = f'''
            select ii.recipe_id, ii.qty, ingr.name
            from ingredient_item ii
            join ingredient ingr
              on ingr.id = ii.ingredient_id
            where ii.recipe_id in {recipe_ids}
            '''
        # query = sa.select([ingredient_item.c.recipe_id, ingredient_item.c.qty, ingredient.c.name]).\
        #     select_from(
        #     ingredient_item.join(ingredient, ingredient.c.id == ingredient_item.c.ingredient_id)
        # ).where(ingredient_item.c.recipe_id.in_(recipe_ids))

        cursor = await conn.execute(raw)
        ingredient_item_records = await cursor.fetchall()
        ingredient_items = [dict(q) for q in ingredient_item_records]
        return ingredient_items
    return []


async def get_pure_recipe_list(conn, limit, offset, where_list, usr, many, favored):
    ''' selects related source and category for recipe '''
    ''' gets number of value=True votes to likes field '''
    ''' gets liked=True if user liked for recipe '''

    # we fetch only liked recipes if favored is true otherwise full list
    fetch_all_recipes = False if favored else True

    if usr:
        alias1 = vote.alias('alias1')
        alias2 = vote.alias('alias2')
        query = sa.select([recipe, source, category, alias2.c.value.label('liked'), sa.func.count(alias1.c.recipe_id).label('likes')], use_labels=True).\
            select_from(
                recipe.join(source, source.c.id == recipe.c.source_id)
                .join(category, category.c.id == recipe.c.category_id)
                .join(
                    alias1,
                    sa.and_(alias1.c.recipe_id == recipe.c.id, alias1.c.value == True),
                    isouter=fetch_all_recipes)
                .join(
                    alias2,
                    sa.and_(alias2.c.recipe_id == recipe.c.id, alias2.c.value == True, alias2.c.user_id == usr['id']),
                    isouter=fetch_all_recipes)
            ).group_by(recipe.c.id, source.c.id, category.c.id, alias2.c.value)
    else:
        query = sa.select([recipe, source, category, sa.func.count(vote.c.recipe_id).label('likes')], use_labels=True).\
            select_from(
                recipe.join(source, source.c.id == recipe.c.source_id)
                .join(category, category.c.id == recipe.c.category_id)
                .join(vote, sa.and_(vote.c.recipe_id == recipe.c.id, vote.c.value == True), isouter=True)
            ).group_by(recipe.c.id, source.c.id, category.c.id)

    for where in where_list:
        query = query.where(where)

    if not many:
        cursor = await conn.execute(query)
        recipe_record = await cursor.fetchone()
        if not recipe_record:
            raise RecordNotFound('No recipe with such id')
        rec = dict(recipe_record)
        return [rec]

    query = query.limit(limit).offset(offset)

    cursor = await conn.execute(query)
    recipe_records = await cursor.fetchall()
    recipes = [dict(q) for q in recipe_records]
    return recipes


async def get_recipe_list_count(conn, where_list, favored=False, usr=None):
    if favored:
        query = sa.select([sa.func.count()]).\
            select_from(
            recipe.join(vote, sa.and_(
                            vote.c.recipe_id == recipe.c.id,
                            vote.c.value == True,
                            vote.c.user_id == usr['id'])))
    else:
        query = sa.select([sa.func.count()]).select_from(recipe)
    for where in where_list:
        query = query.where(where)
    cursor = await conn.execute(query)
    count_record = await cursor.fetchone()
    return count_record[0]


async def comment_recipe(dbengine, data, recipe_id, user):
    async with dbengine.acquire() as conn:
        await validate_recipe(conn, recipe_id)
        validate_comment(data)
        cursor = await conn.execute(
            comment.insert()
                .values(user_id=user['id'],
                        recipe_id=recipe_id,
                        body=data['body'],
                        pub_date=datetime.now().date())
                .returning(comment.c.id))
        comment_record = await cursor.fetchone()

        if not comment_record:
            raise RecordNotFound('Error while creating new comment')


async def vote_recipe(dbengine, recipe_id, user):
    async with dbengine.acquire() as conn:
        await validate_recipe(conn, recipe_id)
        cursor = await conn.execute(
            vote.select()
                .where(vote.c.recipe_id == recipe_id)
                .where(vote.c.user_id == user['id']))
        vote_record = await cursor.fetchone()
        # creates new vote record if there is first vote
        if not vote_record:
            cursor = await conn.execute(
                vote.insert()
                    .values(recipe_id=recipe_id,
                            user_id=user['id'],
                            value=True)
                    .returning(vote.c.id))
            vote_record = await cursor.fetchone()
            cursor.close()
        else:
            value = False if vote_record['value'] else True
            cursor = await conn.execute(
                vote.update()
                    .where(vote.c.recipe_id == recipe_id)
                    .where(vote.c.user_id == user['id'])
                    .values(value=value)
                    .returning(vote.c.id))
            vote_record = await cursor.fetchone()
            cursor.close()

        if not vote_record:
            raise RecordNotFound('Error while creating new vote')


async def login(dbengine, data, jwt_config):
    async with dbengine.acquire() as conn:
        user = await validate_login(conn, data)
        JWT_SECRET = jwt_config['secret']
        JWT_ALGORITHM = jwt_config['algo']
        JWT_EXP_DELTA_SECONDS = jwt_config['exp']
        payload = {
            'user_id': user['id'],
            'exp': datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS)
        }
        jwt_token = jwt.encode(payload, JWT_SECRET, JWT_ALGORITHM)
        return jwt_token


async def register(dbengine, data):
    async with dbengine.acquire() as conn:
        await validate_register(conn, data)
        password_hash = sha256_crypt.hash(data['password'])
        query = users.insert().values(username=data['username'], passwd=password_hash, email=data['email']).returning(users.c.id)
        cursor = await conn.execute(query)
        user_record = await cursor.fetchone()
        if not user_record:
            raise RecordNotFound('There were an error with creating new user')


async def set_userpic(dbengine, filename, user):
    async with dbengine.acquire() as conn:
        cursor = await conn.execute(
            users.update()
                .where(users.c.id == user['id'])
                .values(userpic=filename)
                .returning(users.c.id, users.c.userpic))
        user_record = await cursor.fetchone()
        cursor.close()

        if not user_record:
            raise RecordNotFound('Error while updating userpic')
        return dict(user_record)


async def user_by_id(dbengine, user_id):
    raw = f'''
        select u.id, u.username, u.email, u.superuser, u.userpic 
        from users u
        where u.id = {user_id}
        '''

    async with dbengine.acquire() as conn:
        cursor = await conn.execute(raw)
        user_record = await cursor.fetchone()
        if not user_record:
            raise RecordNotFound('Error while retrieve user record')
        return dict(user_record)

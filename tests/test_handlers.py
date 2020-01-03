from datetime import datetime, timedelta

from recipes.db_tables import recipe, vote, comment
import sqlalchemy as sa


async def test_register(cli, tables_and_data):
    response = await cli.post(
        '/api/register',
        json={'username':'test_user', 'email': 'test@test.test'}
    )
    assert response.status == 400 # no password

    response = await cli.post(
        '/api/register',
        json={'username': 'test_user', 'password': 'qwerty'}
    )
    assert response.status == 400 # no email

    response = await cli.post(
        '/api/register',
        json={'password': 'qwerty', 'email': 'test@test.test'}
    )
    assert response.status == 400 # no username

    response = await cli.post(
        '/api/register',
        json={'username': 'test_user', 'password': 'qwerty', 'email': 'testtest.test'}
    )
    assert response.status == 400 # bad email format

    response = await cli.post(
        '/api/register',
        json={'username': 'test_user', 'password': 'qwerty', 'email': 'test@test.test'}
    )
    assert response.status == 200

    response = await cli.post(
        '/api/register',
        json={'username': 'test_user', 'password': 'qwerty', 'email': 'test_two@test.test'}
    )
    assert response.status == 400 # user with this username already exists

    response = await cli.post(
        '/api/register',
        json={'username': 'test_user_two', 'password': 'qwerty', 'email': 'test@test.test'}
    )
    assert response.status == 400 # user with this email already exists

    response = await cli.post(
        '/api/register',
        json={'username': 'test_user_two', 'password': 'qwerty', 'email': 'test_two@test.test'}
    )
    assert response.status == 200


async def test_login(cli, tables_and_data):
    response = await cli.post(
        '/api/login',
        json={'password': 'qwerty'}
    )
    assert response.status == 400 # no username

    response = await cli.post(
        '/api/login',
        json={'username': 'test_user'}
    )
    assert response.status == 400 # no password

    response = await cli.post(
        '/api/login',
        json={'username': 'test_user', 'password': 'qwerty'}
    )
    assert response.status == 400 # no username in db

    response = await cli.post(
        '/api/register',
        json={'username': 'test_user', 'password': 'qwerty', 'email': 'test@test.test'}
    )
    assert response.status == 200

    response = await cli.post(
        '/api/login',
        json={'username': 'test_user', 'password': 'qwertyq'}
    )
    assert response.status == 400 # bad password

    response = await cli.post(
        '/api/login',
        json={'username': 'test_user', 'password': 'qwerty'}
    )
    assert 'token' in await response.text()
    assert response.status == 200


async def test_vote_recipe(cli, tables_and_data):
    response = await cli.post(
        '/api/recipes/340/vote'
    )
    assert response.status == 401 # no authorization

    response = await cli.post(
        '/api/register',
        json={'username': 'test_user', 'password': 'qwerty', 'email': 'test@test.test'}
    )
    assert response.status == 200

    response = await cli.post(
        '/api/login',
        json={'username': 'test_user', 'password': 'qwerty'}
    )
    assert response.status == 200
    token = (await response.json())['token']

    response = await cli.post(
        '/api/recipes/340/vote',
        headers = {'authorization_jwt': token}
    )
    assert response.status == 200
    async with cli.server.app['db'].acquire() as conn:
        cursor = await conn.execute(vote.select()
                                    .where(vote.c.recipe_id==340)
                                    .where(vote.c.user_id==1))
        vote_record = await cursor.fetchone()
        assert vote_record['value'] == True


    response = await cli.post(
        '/api/recipes/340/vote',
        headers = {'authorization_jwt': token}
    )
    assert response.status == 200
    async with cli.server.app['db'].acquire() as conn:
        cursor = await conn.execute(vote.select()
                                    .where(vote.c.recipe_id==340)
                                    .where(vote.c.user_id==1))
        vote_record = await cursor.fetchone()
        assert vote_record['value'] == False


    response = await cli.post(
        '/api/recipes/1/vote',
        headers = {'authorization_jwt': token}
    )
    assert response.status == 400 # bad recipe id


async def test_comment_recipe(cli, tables_and_data):
    response = await cli.post(
        '/api/recipes/348/comment'
    )
    assert response.status == 401 #

    response = await cli.post(
        '/api/register',
        json={'username': 'test_user', 'password': 'qwerty', 'email': 'test@test.test'}
    )
    assert response.status == 200

    response = await cli.post(
        '/api/login',
        json={'username': 'test_user', 'password': 'qwerty'}
    )
    assert response.status == 200
    token = (await response.json())['token']

    response = await cli.post(
        '/api/recipes/348/comment',
        headers = {'authorization_jwt': token}
    )
    assert response.status != 200 # no body

    response = await cli.post(
        '/api/recipes/348/comment',
        headers = {'authorization_jwt': token},
        json={'body': 'Very bad recipe, I dont like it'}
    )
    assert response.status == 200
    async with cli.server.app['db'].acquire() as conn:
        cursor = await conn.execute(sa.select([sa.func.count()])
                                    .select_from(comment)
                                        .where(comment.c.recipe_id==348)
                                        .where(comment.c.user_id==1))
        count_record = await cursor.fetchone()
        assert count_record[0] == 1


    response = await cli.post(
        '/api/recipes/348/comment',
        headers = {'authorization_jwt': token},
        json={'body': 'I want to repeat - this recipe is awful! I hate it!'}
    )
    assert response.status == 200
    async with cli.server.app['db'].acquire() as conn:
        cursor = await conn.execute(sa.select([sa.func.count()])
                                    .select_from(comment)
                                        .where(comment.c.recipe_id==348)
                                        .where(comment.c.user_id==1))
        count_record = await cursor.fetchone()
        assert count_record[0] == 2


    response = await cli.post(
        '/api/recipes/1/comment',
        headers = {'authorization_jwt': token},
        json={'body': 'Some comment'}
    )
    assert response.status == 400 # bad recipe id


async def test_recipes(cli, tables_and_data):
    recipe_fields = ['recipe_id', 'recipe_title', 'recipe_slug', 'recipe_descr', 'recipe_url',
                     'recipe_prep_time', 'recipe_main_image', 'recipe_pub_date', 'recipe_source_id',
                     'recipe_category_id', 'source_name', 'source_url', 'category_name',
                     'category_code', 'likes', 'ingredients', 'comments']
    recipe_fields_authorized = recipe_fields + ['liked']

    # w/o authorization
    response = await cli.get('/api/recipes')
    assert response.status == 200
    response_data = await response.json()
    # checks fields in response data
    assert 'count' in response_data
    assert 'next' in response_data
    assert 'results' in response_data
    one_recipe = response_data['results'][0]
    assert len(response_data['results']) == 20 # default limit
    assert response_data['next'] == '/api/recipes?offset=20'
    # checks fields in every recipe object
    for field in recipe_fields:
        assert field in one_recipe
    async with cli.server.app['db'].acquire() as conn:
        cursor = await conn.execute(sa.select([sa.func.count()])
                                    .select_from(
                                        recipe))
        count_record = await cursor.fetchone()
        assert count_record[0] == response_data['count']

    # check filters
    response = await cli.get('/api/recipes?category=1')
    assert response.status == 200
    response_data = await response.json()
    for one_recipe in response_data['results']:
        assert one_recipe['category_id'] == 1

    response = await cli.get('/api/recipes?prep_time=45')
    assert response.status == 200
    response_data = await response.json()
    test_timedelta = timedelta(minutes=45)
    for one_recipe in response_data['results']:
        one_recipe_timedelta = timedelta(hours=int(one_recipe['recipe_prep_time'].split(':')[0]),
                                        minutes=int(one_recipe['recipe_prep_time'].split(':')[0]),
                                        seconds=int(one_recipe['recipe_prep_time'].split(':')[0]))
        assert one_recipe_timedelta <= test_timedelta

    response = await cli.get('/api/recipes?from=1-1-2008')
    assert response.status == 200
    response_data = await response.json()
    test_date = datetime(year=2008, month=1, day=1).date()
    for one_recipe in response_data['results']:
        one_recipe_date = datetime.strptime(one_recipe['recipe_pub_date'], '%Y-%m-%d').date()
        assert one_recipe_date >= test_date

    response = await cli.get('/api/recipes?to=1-12-2018')
    assert response.status == 200
    response_data = await response.json()
    test_date = datetime(year=2018, month=12, day=1).date()
    for one_recipe in response_data['results']:
        one_recipe_date = datetime.strptime(one_recipe['recipe_pub_date'], '%Y-%m-%d').date()
        assert one_recipe_date <= test_date

    response = await cli.get('/api/recipes?to=1-12-2018&from=1-1-2008')
    assert response.status == 200
    response_data = await response.json()
    test_date_to = datetime(year=2018, month=12, day=1).date()
    test_date_from = datetime(year=2008, month=1, day=1).date()
    for one_recipe in response_data['results']:
        one_recipe_date = datetime.strptime(one_recipe['recipe_pub_date'], '%Y-%m-%d').date()
        assert one_recipe_date <= test_date_to
        assert one_recipe_date >= test_date_from

    response = await cli.get('/api/recipes?limit=40')
    assert response.status == 200
    response_data = await response.json()
    assert len(response_data['results']) == 40

    response = await cli.get('/api/recipes?limit=40&offset=20')
    assert response.status == 200
    response_data = await response.json()
    assert len(response_data['results']) == 40

    response = await cli.get('/api/recipes?to=1-12-2018&from=1-1-2008&category=2&limit=5&offset=5')
    assert response.status == 200
    response_data = await response.json()
    test_date_to = datetime(year=2018, month=12, day=1).date()
    test_date_from = datetime(year=2008, month=1, day=1).date()
    for one_recipe in response_data['results']:
        one_recipe_date = datetime.strptime(one_recipe['recipe_pub_date'], '%Y-%m-%d').date()
        assert one_recipe_date <= test_date_to
        assert one_recipe_date >= test_date_from
        assert one_recipe['recipe_category_id'] == 2
    assert len(response_data['results']) <= 5

    # /w authorization
    response = await cli.post(
        '/api/register',
        json={'username': 'test_user', 'password': 'qwerty', 'email': 'test@test.test'}
    )
    assert response.status == 200
    response = await cli.post(
        '/api/login',
        json={'username': 'test_user', 'password': 'qwerty'}
    )
    assert response.status == 200
    token = (await response.json())['token']

    response = await cli.get('/api/recipes', headers = {'authorization_jwt': token})
    assert response.status == 200
    response_data = await response.json()
    assert 'count' in response_data
    assert 'next' in response_data
    assert 'results' in response_data
    one_recipe = response_data['results'][0]
    assert len(response_data['results']) == 20 # default limit
    assert response_data['next'] == '/api/recipes?offset=20'
    for field in recipe_fields_authorized:
        assert field in one_recipe
    async with cli.server.app['db'].acquire() as conn:
        cursor = await conn.execute(sa.select([sa.func.count()])
                                    .select_from(
                                        recipe))
        count_record = await cursor.fetchone()
        assert count_record[0] == response_data['count']

    response = await cli.get('/api/recipes', headers = {'authorization_jwt': token[:-1]})
    assert response.status == 400 # bad token

    # checks 'likes' incrementing and 'liked' field for user after voting
    response = await cli.post(
        '/api/recipes/340/vote',
        headers = {'authorization_jwt': token}
    )
    assert response.status == 200
    response = await cli.get('/api/recipes?limit=140', headers = {'authorization_jwt': token})
    assert response.status == 200
    response_data = await response.json()
    for one_recipe in response_data['results']:
        if one_recipe['recipe_id'] == 340:
            assert one_recipe['likes'] == 1
            assert one_recipe['liked'] == True

    # checks 'likes' increment after voting
    response = await cli.get('/api/recipes?limit=140')
    assert response.status == 200
    response_data = await response.json()
    for one_recipe in response_data['results']:
        if one_recipe['recipe_id'] == 340:
            assert one_recipe['likes'] == 1

    response = await cli.post(
        '/api/recipes/340/vote',
        headers = {'authorization_jwt': token}
    )
    assert response.status == 200
    response = await cli.get('/api/recipes?limit=140', headers = {'authorization_jwt': token})
    assert response.status == 200
    response_data = await response.json()
    for one_recipe in response_data['results']:
        if one_recipe['recipe_id'] == 340:
            assert one_recipe['liked'] != True

    response = await cli.get('/api/recipes?limit=140')
    assert response.status == 200
    response_data = await response.json()
    for one_recipe in response_data['results']:
        if one_recipe['recipe_id'] == 340:
            assert one_recipe['likes'] == 0

    # checks 'comments' field after commenting
    response = await cli.post(
        '/api/recipes/348/comment',
        headers = {'authorization_jwt': token},
        json={'body': 'I love this so much!'}
    )
    assert response.status == 200
    response = await cli.get('/api/recipes?limit=140', headers = {'authorization_jwt': token})
    assert response.status == 200
    response_data = await response.json()
    for one_recipe in response_data['results']:
        if one_recipe['recipe_id'] == 348:
            assert len(one_recipe['comments']) == 1
            assert one_recipe['comments'][0]['body'] == 'I love this so much!'

    # checks 'comments' field as unauthorized
    response = await cli.get('/api/recipes?limit=140')
    assert response.status == 200
    response_data = await response.json()
    for one_recipe in response_data['results']:
        if one_recipe['recipe_id'] == 348:
            assert len(one_recipe['comments']) == 1
            assert one_recipe['comments'][0]['body'] == 'I love this so much!'

    response = await cli.post(
        '/api/recipes/348/comment',
        headers = {'authorization_jwt': token},
        json={'body': 'I love this so much![2]'}
    )
    assert response.status == 200
    response = await cli.get('/api/recipes?limit=140', headers = {'authorization_jwt': token})
    assert response.status == 200
    response_data = await response.json()
    for one_recipe in response_data['results']:
        if one_recipe['recipe_id'] == 348:
            assert len(one_recipe['comments']) == 2
            assert 'I love this so much!' in [comment['body'] for comment in one_recipe['comments']]
            assert 'I love this so much![2]' in [comment['body'] for comment in one_recipe['comments']]

    response = await cli.get('/api/recipes?limit=140')
    assert response.status == 200
    response_data = await response.json()
    for one_recipe in response_data['results']:
        if one_recipe['recipe_id'] == 348:
            assert len(one_recipe['comments']) == 2
            assert 'I love this so much!' in [comment['body'] for comment in one_recipe['comments']]
            assert 'I love this so much![2]' in [comment['body'] for comment in one_recipe['comments']]


async def test_favored(cli, tables_and_data):
    response = await cli.get('/api/recipes/favored')
    assert response.status == 401 # no authorization

    response = await cli.post(
        '/api/register',
        json={'username': 'test_user', 'password': 'qwerty', 'email': 'test@test.test'}
    )
    assert response.status == 200
    response = await cli.post(
        '/api/login',
        json={'username': 'test_user', 'password': 'qwerty'}
    )
    assert response.status == 200
    token = (await response.json())['token']

    response = await cli.get('/api/recipes/favored', headers = {'authorization_jwt': token})
    assert response.status == 200
    response_data = await response.json()
    assert 'count' in response_data
    assert 'next' in response_data
    assert 'results' in response_data
    assert len(response_data['results']) == 0 # have no liked recipes yet

    # add 4 likes
    for recipe_id in [340, 348, 350, 470]:
        response = await cli.post(
            f'/api/recipes/{recipe_id}/vote',
            headers = {'authorization_jwt': token}
        )
        assert response.status == 200
    response = await cli.get('/api/recipes/favored', headers = {'authorization_jwt': token})
    assert response.status == 200
    response_data = await response.json()
    assert len(response_data['results']) == 4
    for one_recipe in response_data['results']:
        assert one_recipe['liked'] == True

    # remove one like
    response = await cli.post(
        f'/api/recipes/340/vote',
        headers={'authorization_jwt': token}
    )
    assert response.status == 200
    response = await cli.get('/api/recipes/favored', headers = {'authorization_jwt': token})
    assert response.status == 200
    response_data = await response.json()
    assert len(response_data['results']) == 3


async def test_recipe_detail(cli, tables_and_data):
    recipe_fields = ['recipe_id', 'recipe_title', 'recipe_slug', 'recipe_descr', 'recipe_url',
                     'recipe_prep_time', 'recipe_main_image', 'recipe_pub_date', 'recipe_source_id',
                     'recipe_category_id', 'source_name', 'source_url', 'category_name',
                     'category_code', 'likes', 'ingredients', 'comments']
    recipe_fields_authorized = recipe_fields + ['liked']

    # w/o authorization
    response = await cli.get('/api/recipes/340')
    assert response.status == 200
    response_data = await response.json()
    # checks fields in recipe object
    for field in recipe_fields:
        assert field in response_data

    response = await cli.get('/api/recipes/1')
    assert response.status == 400 # bad recipe id

    # /w authorization
    response = await cli.post(
        '/api/register',
        json={'username': 'test_user', 'password': 'qwerty', 'email': 'test@test.test'}
    )
    assert response.status == 200
    response = await cli.post(
        '/api/login',
        json={'username': 'test_user', 'password': 'qwerty'}
    )
    assert response.status == 200
    token = (await response.json())['token']

    response = await cli.get('/api/recipes/340', headers = {'authorization_jwt': token})
    assert response.status == 200
    response_data = await response.json()
    for field in recipe_fields_authorized:
        assert field in response_data

    # checks 'likes' incrementing and 'liked' after voting
    response = await cli.post(
        f'/api/recipes/340/vote',
        headers={'authorization_jwt': token}
    )
    assert response.status == 200
    response = await cli.get('/api/recipes/340', headers = {'authorization_jwt': token})
    assert response.status == 200
    response_data = await response.json()
    assert response_data['liked'] == True
    assert response_data['likes'] == 1

    # checks 'likes' incrementing after voting as unauthorized
    response = await cli.get('/api/recipes/340')
    assert response.status == 200
    response_data = await response.json()
    assert response_data['likes'] == 1

    # remove one like
    response = await cli.post(
        f'/api/recipes/340/vote',
        headers={'authorization_jwt': token}
    )
    assert response.status == 200
    response = await cli.get('/api/recipes/340')
    assert response.status == 200
    response_data = await response.json()
    assert response_data['likes'] == 0

    # checks 'comments' after commenting
    response = await cli.post(
        f'/api/recipes/340/comment',
        json={'body': 'some comment'},
        headers={'authorization_jwt': token}
    )
    assert response.status == 200
    response = await cli.get('/api/recipes/340', headers = {'authorization_jwt': token})
    assert response.status == 200
    response_data = await response.json()
    assert len(response_data['comments']) == 1

    # checks 'comments' after commenting as unauthorized
    response = await cli.get('/api/recipes/340')
    assert response.status == 200
    response_data = await response.json()
    assert len(response_data['comments']) == 1

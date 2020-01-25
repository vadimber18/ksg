import pytest

from recipes.main import init_app
from recipes.settings import TEST_CONFIG
from init_db import (
    setup_db,
    teardown_db,
    create_tables,
    sample_data,
    drop_tables
)



@pytest.fixture
async def cli(loop, aiohttp_client, db):
    app = await init_app(testing=True)
    return await aiohttp_client(app)


@pytest.fixture(scope='module')
def db():
    setup_db(TEST_CONFIG['postgres'])
    yield
    teardown_db(TEST_CONFIG['postgres'])


@pytest.fixture
def tables_and_data():
    create_tables()
    sample_data()
    yield
    drop_tables()

@pytest.fixture
async def token(cli):
    token = await get_token(cli)
    yield token

async def get_token(cli):
    response = await cli.post(
        '/api/register',
        json={'username': 'test_user', 'password': 'qwerty', 'email': 'test@test.test'}
    )
    assert response.status == 201

    response = await cli.post(
        '/api/login',
        json={'username': 'test_user', 'password': 'qwerty'}
    )
    assert response.status == 200
    token = (await response.json())['token']
    return token
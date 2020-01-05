import json
from datetime import datetime, timedelta

from sqlalchemy import create_engine, MetaData

from recipes.settings import BASE_DIR, CONFIG, TEST_CONFIG

from recipes.db_tables import users, source, category, ingredient, ingredient_item, recipe, comment, vote


DSN = "postgresql://{user}:{password}@{host}:{port}/{database}"

USER_CONFIG = CONFIG
USER_DB_URL = DSN.format(**USER_CONFIG['postgres'])
user_engine = create_engine(USER_DB_URL)
admin_engine = create_engine(USER_DB_URL, isolation_level='AUTOCOMMIT')

TEST_CONFIG = TEST_CONFIG
TEST_DB_URL = DSN.format(**TEST_CONFIG['postgres'])
test_engine = create_engine(TEST_DB_URL)

FIXTURES_PATH = f'{BASE_DIR}/tests/json_fixtures'


def setup_db(config):
    db_name = config['database']
    db_user = config['user']
    db_pass = config['password']

    conn = admin_engine.connect()
    conn.execute(f'DROP DATABASE IF EXISTS {db_name}')
    conn.execute(f'DROP ROLE IF EXISTS {db_user}')
    conn.execute(f"CREATE USER {db_user} WITH PASSWORD '{db_pass}'")
    conn.execute(f"CREATE DATABASE {db_name} ENCODING 'UTF8'")
    conn.execute(f'GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user}')
    conn.close()


def teardown_db(config):
    db_name = config['database']
    db_user = config['user']

    conn = admin_engine.connect()
    conn.execute(f"""
      SELECT pg_terminate_backend(pg_stat_activity.pid)
      FROM pg_stat_activity
      WHERE pg_stat_activity.datname = '{db_name}'
        AND pid <> pg_backend_pid();""")
    conn.execute(f'DROP DATABASE IF EXISTS {db_name}')
    conn.execute(f'DROP ROLE IF EXISTS {db_user}')
    conn.close()


def create_tables(engine=test_engine):
    meta = MetaData()
    meta.create_all(bind=engine, tables=[users, source, category, ingredient, ingredient_item, recipe, comment, vote])


def drop_tables(engine=test_engine):
    meta = MetaData()
    meta.drop_all(bind=engine, tables=[users, source, category, ingredient, ingredient_item, recipe, comment, vote])


def insert_from_fixtures(conn, fixture_filenames):
    for filename in fixture_filenames:
        table = eval(filename.split('.')[0])
        with open(f'{FIXTURES_PATH}/{filename}') as f:
            data = json.load(f)
        for record in data:
            # make sure there is no such record already
            query = table.select().where(table.c.id == record['id'])
            cursor = conn.execute(query)
            real_record = cursor.fetchone()
            if real_record:
                continue
            if filename == 'recipe.json':
                if record['pub_date']:
                    record['pub_date'] = datetime.strptime(record['pub_date'], '%Y-%m-%d')
                if record['prep_time']:
                    record['prep_time'] = timedelta(hours=int(record['prep_time'].split(':')[0]),
                                                    minutes=int(record['prep_time'].split(':')[0]),
                                                    seconds=int(record['prep_time'].split(':')[0])
                                                    )
            conn.execute(table.insert(), record)


def sample_data(engine=test_engine):
    conn = engine.connect()

    # we always need categories
    insert_from_fixtures(conn, ['category.json'])

    if engine==test_engine:
        fixture_filenames = ['source.json', 'recipe.json', 'ingredient.json', 'ingredient_item.json']
        insert_from_fixtures(conn, fixture_filenames)

    conn.close()


if __name__ == '__main__':

    #setup_db(USER_CONFIG['postgres'])
    create_tables(engine=user_engine)
    sample_data(engine=user_engine)
    # drop_tables(engine=user_engine)
    # teardown_db(USER_CONFIG['postgres'])

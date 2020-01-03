import os
import pathlib


BASE_DIR = pathlib.Path(__file__).parent.parent


CONFIG = {
    'postgres': {
        'database': os.environ.get('POSTGRES_DB', 'recipes'),
        'password': os.environ.get('POSTGRES_PASSWORD', 'recipes_pass'),
        'user': os.environ.get('POSTGRES_USER', 'recipes_user'),
        'host': os.environ.get('POSTGRES_HOST', 'postgres'),
        'port': int(os.environ.get('POSTGRES_PORT', 5432)),
        'minsize': int(os.environ.get('POSTGRES_MINSIZE', 1)),
        'maxsize': int(os.environ.get('POSTGRES_MAXSIZE', 5))
    },
    'jwt': {
        'secret': os.environ.get('JWT_SECRET', 'somesecret'),
        'algo': os.environ.get('JWT_ALGO', 'HS256'),
        'exp': int(os.environ.get('JWT_EXP', 3600)),
    },
    'aiohttp-admin':{
        'user': os.environ.get('AIOHTTPADMIN_USER', 'admin'),
        'password': os.environ.get('AIOHTTPADMIN_PASSWORD', 'admin'),
    },
    'host': os.environ.get('AIO_HOST', '127.0.0.1'),
    'port': int(os.environ.get('AIO_PORT', 8080)),
    'debug': bool(os.environ.get('DEBUG', False)),
}

TEST_CONFIG = {
    'postgres': {
        'database': os.environ.get('TEST_POSTGRES_DB', 'test_recipes'),
        'password': os.environ.get('TEST_POSTGRES_PASSWORD', 'test_recipes_pass'),
        'user': os.environ.get('TEST_POSTGRES_USER', 'test_recipes_user'),
        'host': os.environ.get('POSTGRES_HOST', 'postgres'),
        'port': int(os.environ.get('POSTGRES_PORT', 5432)),
        'minsize': int(os.environ.get('POSTGRES_MINSIZE', 1)),
        'maxsize': int(os.environ.get('POSTGRES_MAXSIZE', 5))
    },
    'jwt': {
        'secret': os.environ.get('JWT_SECRET', 'somesecret'),
        'algo': os.environ.get('JWT_ALGO', 'HS256'),
        'exp': int(os.environ.get('JWT_EXP', 3600)),
    },
    'aiohttp-admin':{
        'user': os.environ.get('AIOHTTPADMIN_USER', 'admin'),
        'password': os.environ.get('AIOHTTPADMIN_PASSWORD', 'admin'),
    },
    'host': os.environ.get('AIO_HOST', '127.0.0.1'),
    'port': int(os.environ.get('AIO_PORT', 8080)),
    'debug': bool(os.environ.get('DEBUG', False)),
}
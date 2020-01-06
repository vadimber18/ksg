from sqlalchemy import (
    MetaData, Table, Column, ForeignKey,
    Integer, String, Date, Text, Interval, Boolean
)


meta = MetaData()


users = Table(
    'users', meta,

    Column('id', Integer, primary_key=True),
    Column('username', String(64), nullable=False),
    Column('email', String(120), nullable=False, unique=True),
    Column('passwd', String(128), nullable=False),
    Column('superuser', Boolean, default=False),
    Column('userpic', String(256), nullable=True)
)

source = Table(
    'source', meta,

    Column('id', Integer, primary_key=True),
    Column('name', String(120), nullable=False),
    Column('url', String(120), nullable=False, unique=True)
)

category = Table(
    'category', meta,

    Column('id', Integer, primary_key=True),
    Column('name', String(120), nullable=False),
    Column('code', String(120), unique=True)
)

ingredient = Table(
    'ingredient', meta,

    Column('id', Integer, primary_key=True),
    Column('name', String(120), nullable=False)
)

ingredient_item = Table(
    'ingredient_item', meta,

    Column('id', Integer, primary_key=True),
    Column('recipe_id',
           Integer,
           ForeignKey('recipe.id', ondelete='CASCADE')), # related ingrs?
    Column('ingredient_id',
           Integer,
           ForeignKey('ingredient.id', ondelete='CASCADE')),
    Column('qty', String(120))
)


recipe = Table(
    'recipe', meta,

    Column('id', Integer, primary_key=True),
    Column('title', String(120), nullable=False),
    Column('slug', String(120), index=True, unique=True),
    Column('descr', Text),
    Column('url', String(120), nullable=False),
    Column('prep_time', Interval),
    Column('main_image', String(120)),
    Column('pub_date', Date),
    Column('source_id',
           Integer,
           ForeignKey('source.id', ondelete='CASCADE')),
    Column('category_id',
           Integer,
           ForeignKey('category.id', ondelete='CASCADE'))
)

comment = Table(
    'comment', meta,

    Column('id', Integer, primary_key=True),
    Column('user_id',
           Integer,
           ForeignKey('users.id', ondelete='CASCADE')),
    Column('recipe_id',
           Integer,
           ForeignKey('recipe.id', ondelete='CASCADE')),
    Column('body', String(120), nullable=False),
    Column('pub_date', Date, nullable=False)
)


vote = Table(
    'vote', meta,

    Column('id', Integer, primary_key=True),
    Column('user_id',
           Integer,
           ForeignKey('users.id', ondelete='CASCADE')),
    Column('recipe_id',
           Integer,
           ForeignKey('recipe.id', ondelete='CASCADE')),
    Column('value',
           Boolean)
)
import aiohttp_admin
import aiohttp_security

from aiohttp_admin.contrib import models, Schema
from aiohttp_admin.backends.sa import PGResource
from aiohttp_admin.security import DummyAuthPolicy, DummyTokenIdentityPolicy

from recipes.db_tables import users, category, source, ingredient, ingredient_item, recipe, comment, vote


schema = Schema()


def setup_admin(app, pg):
    admin = aiohttp_admin._setup(
        app,
        title='Blog admin',
        schema=schema,
        db=pg,
    )

    # setup dummy auth and identity
    ident_policy = DummyTokenIdentityPolicy()
    auth_policy = DummyAuthPolicy(username=app['config']['aiohttp-admin']['user'],
                                  password=app['config']['aiohttp-admin']['password'])
    aiohttp_security.setup(admin, ident_policy, auth_policy)

    app.add_subapp('/admin', admin)


@schema.register
class Users(models.ModelAdmin):
    fields = ('id', 'username', 'email', 'password')

    class Meta:
        resource_type = PGResource
        table = users

@schema.register
class Source(models.ModelAdmin):
    fields = ('id', 'name', 'url')

    class Meta:
        resource_type = PGResource
        table = source


@schema.register
class Category(models.ModelAdmin):
    fields = ('id', 'name', 'code')

    class Meta:
        resource_type = PGResource
        table = category


@schema.register
class Ingredient(models.ModelAdmin):
    fields = ('id', 'name')

    class Meta:
        resource_type = PGResource
        table = ingredient


@schema.register
class Ingredient_item(models.ModelAdmin):
    fields = ('id', 'recipe_id', 'ingredient_id', 'qty')

    class Meta:
        resource_type = PGResource
        table = ingredient_item


@schema.register
class Comment(models.ModelAdmin):
    fields = ('id', 'user_id', 'recipe_id', 'body', 'pub_date')

    class Meta:
        resource_type = PGResource
        table = comment


@schema.register
class Vote(models.ModelAdmin):
    fields = ('id', 'user_id', 'recipe_id', 'value')

    class Meta:
        resource_type = PGResource
        table = vote

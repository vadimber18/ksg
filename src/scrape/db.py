from recipes import db_tables as recipes_db

import asyncio

from slugify import slugify


async def update_or_register_source(dbengine, name, url):
    if url[-1] == '/':
        url = url[:-1]

    async with dbengine.acquire() as conn:
        # Create or update the object from the DB
        cursor = await conn.execute(
            recipes_db.source.update()
                .where(recipes_db.source.c.url == url)
                .values(name=name, url=url)
                .returning(recipes_db.source.c.id, recipes_db.source.c.url))
        source_record = await cursor.fetchone()
        if not source_record:
            cursor = await conn.execute(
                recipes_db.source.insert()
                    .values(name=name, url=url)
                    .returning(recipes_db.source.c.id, recipes_db.source.c.url))
            source_record = await cursor.fetchone()
        return source_record


async def get_recipe_by_url(dbengine, url):
    async with dbengine.acquire() as conn:
        cursor = await conn.execute(recipes_db.recipe.select() \
                                    .where(recipes_db.recipe.c.url == url))
        recipe_record = await cursor.fetchone()
        return recipe_record

async def get_all_sources(dbengine):
    async with dbengine.acquire() as conn:
        cursor = await conn.execute(recipes_db.source.select())
        source_records = await cursor.fetchall()
        return source_records


async def save_recipe(dbengine, task_result, recipe, recipe_source):
    recipe['source'] = recipe_source['id']
    category_code = recipe['category']

    async with dbengine.acquire() as conn:
        cursor = await conn.execute(recipes_db.category.select() \
                                    .where(recipes_db.category.c.code == category_code))
        record = await cursor.fetchone()
        cursor.close() # or await? waiting a new release of aiopg anyways, they use sync .close()
        if not record:
            task_result.update({'exc_number': task_result['exc_number'] + 1})
            raise Exception('Couldnt get category from code specified in module')
        recipe['category'] = record['id']


        slug = slugify(recipe['title'])
        # append '-1', '-2' and so on if there are repeating slugs
        cursor = await conn.execute(recipes_db.recipe.select() \
                                    .where(recipes_db.recipe.c.slug == slug))
        record = await cursor.fetchone()
        cursor.close()
        if record is not None:
            suffix = 0
            while record is not None:
                suffix += 1
                slug = f'{slug}-{str(suffix)}'
                cursor = await conn.execute(recipes_db.recipe.select() \
                                    .where(recipes_db.recipe.c.slug == slug))
                record = await cursor.fetchone()
                cursor.close()

        # make main image url absolute
        if recipe['main_image'] is not None:
            if recipe['main_image'].startswith('/'):
                source_url = recipe_source['url']
                if source_url.endswith('/'):
                    source_url = source_url[:-1]
                recipe['main_image'] = source_url + recipe['main_image']

        cursor = await conn.execute(
            recipes_db.recipe.insert()
                .values(title=recipe['title'], url=recipe['url'], descr=recipe['text'],
                        pub_date=recipe['pub_date'], main_image=recipe['main_image'],
                        source_id=recipe['source'], category_id=recipe['category'],
                        slug=slug, prep_time=recipe['prep_time'])
                .returning(recipes_db.recipe.c.id, recipes_db.recipe.c.slug))
        record = await cursor.fetchone()
        cursor.close()
        if not record:
            task_result.update({'exc_number': task_result['exc_number'] + 1})
            raise Exception('Recipe didnt saved for some reason')

        # async adding ingredient items to recipe
        # use semaphore to limit number of concurrent tasks
        sem = asyncio.Semaphore(3)
        tasks = [semaphored_function(sem, save_ingredient_item, dbengine, record['id'], ingredient) for ingredient in recipe['ingredients'].items()]
        try:
            await asyncio.wait(tasks)
        except Exception as e:
            print (e)

        task_result.update({'recipes_saved': task_result['recipes_saved'] + 1})
        print ('recipe saved: ', record['slug'])


async def save_ingredient_item(dbengine, recipe_id, ingredient):
    async with dbengine.acquire() as conn:
        cursor = await conn.execute(recipes_db.ingredient.select() \
                                    .where(recipes_db.ingredient.c.name == ingredient[0]))
        record = await cursor.fetchone()
        cursor.close()
        if not record:
            cursor = await conn.execute(
                recipes_db.ingredient.insert()
                    .values(name=ingredient[0])
                    .returning(recipes_db.ingredient.c.id))
            record = await cursor.fetchone()
            cursor.close()
            if not record:
                raise Exception('Error while saving new ingredient')
        ingredient_id = record['id']

        cursor = await conn.execute(
            recipes_db.ingredient_item.insert()
                .values(recipe_id=recipe_id,
                        ingredient_id=ingredient_id,
                        qty=ingredient[1])
                .returning(recipes_db.ingredient_item.c.id))
        record = await cursor.fetchone()
        cursor.close()
        if not record:
            raise Exception('Error while saving new ingredient_item')

async def semaphored_function(semaphore, function, *func_args):
    async with semaphore:
        return await function(*func_args)

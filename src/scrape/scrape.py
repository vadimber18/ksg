from .parsing import parse_recipe_page, retrieve_recipes_links

import copy
import pkgutil
import importlib
import traceback
import logging

import asyncio

from . import db

log = logging.getLogger(__name__)


class RecipeUpdater:

    DEFAULT_PARSING_RULES = {
        'title': None,
        'text': None,
        'text_finally_exclude_regexes': [],
        'text_exclude_paragraphs_with_classes': [],
        'text_exclude_paragraphs_containing': [],
        'text_auto_cleanup': True,
        'main_image': 'heuristic',
        'pub_date': None,
        'pub_date_preprocessor': None,
        'pub_date_format': None,
        'ingredients': lambda soup: None,  # ONLY callbacks supported
        'prep_time': lambda soup: None,  # ONLY callbacks supported
        'timeout': 3,

        'engine': 'bs',
        'encoding': None,
    }

    DEFAULT_LINK_RETRIEVAL_RULES = {
        'timeout': 3,
        'callback': None,
        'links_selectors': [],
        'links_pages': ['/'],
        'engine': 'bs',
    }

    # Mandatory settings
    SOURCE_NAME = None
    SOURCE_URL = None  # Serves as a db index, so setting it only once is recommended
    SOURCE_DISABLED = False

    def _make_links_pages_absolute(self):
        for i, links_page in enumerate(self.LINK_RETRIEVAL_RULES['links_pages']):
            if type(links_page) == dict:
                if '.' not in links_page['url'] or 'http' not in links_page['url']:
                    if links_page['url'][0] != '/':
                        links_page['url'] = '/' + links_page['url']
                    links_page['url'] = self.SOURCE_URL + links_page['url']
            elif '.' not in links_page or 'http' not in links_page:
                if links_page[0] != '/':
                    links_page = '/' + links_page
                links_page = self.SOURCE_URL + links_page
            self.LINK_RETRIEVAL_RULES['links_pages'][i] = links_page

    def __init__(self):
        # update static members with configured values
        temp_rules = copy.deepcopy(self.DEFAULT_PARSING_RULES)
        temp_rules.update(self.PARSING_RULES)
        self.PARSING_RULES = temp_rules

        temp_rules = copy.deepcopy(self.DEFAULT_LINK_RETRIEVAL_RULES)
        temp_rules.update(self.LINK_RETRIEVAL_RULES)
        self.LINK_RETRIEVAL_RULES = temp_rules

        # make absolute links out of short links to recipe pages
        self._make_links_pages_absolute()

    async def _init(self, request, standalone=False):
        # we can implement factory btw, but thats still ok
        if standalone:
            self.source = None
        else:
            self.source = await db.update_or_register_source(request.app['db'], self.SOURCE_NAME, self.SOURCE_URL)
        self.standalone = standalone

    async def collect_recipes(self, request):
        recipes = []

        print('Trying to retrieve links...')
        try:
            links = await retrieve_recipes_links(self.LINK_RETRIEVAL_RULES)
        except Exception:
            print(f'Unable to collect links for {self.SOURCE_NAME}.')
            return recipes

        if not self.standalone:
            new_links = {}
            for link in links:
                record = await db.get_recipe_by_url(request.app['db'], link)
                if not record:
                    new_links.update({link:links[link]})

            links = new_links

        # parse recipes pages synchronously otherwise it will be DDoS
        for i, link in enumerate(links):
            print('[{}/{}] Fetching recipes for {}...'.format(i + 1, len(links), self.SOURCE_NAME))
            try:
                recipes.append(await parse_recipe_page(link, links[link], self.PARSING_RULES))
            except Exception:
                continue

        # asynchronously variation
        # tasks = [parse_recipe_page(recipes, link, links[link], self.PARSING_RULES) for i, link in enumerate(links)]
        # await asyncio.wait(tasks)

        recipes = [entry for entry in recipes if entry['title'] is not None and entry['title'] != '']
        print(len(recipes))
        return recipes

    async def save_recipes(self, request, recipes):
        if self.standalone:
            print(recipes)
        else:
            result = {'recipes_collected': len(recipes), 'exc_number': 0, 'recipes_saved': 0}
            # asynchronously variation
            # use semaphore to limit number of concurrent tasks
            sem = asyncio.Semaphore(3)
            tasks = [db.semaphored_function(sem, db.save_recipe, request.app['db'], result, recipes[i], self.source) for i, entry in enumerate(recipes)]
            try:
                await asyncio.wait(tasks)
            except Exception as e:
                print(e)
            return result


async def process_module(request, module_name):
    recipes_updater = importlib.import_module('.scrapers.' + module_name, 'scrape').SourceUpdater()
    await recipes_updater._init(request)
    print(module_name)
    if not recipes_updater.SOURCE_DISABLED:
        try:
            recipes = await recipes_updater.collect_recipes(request)
            task_result = await recipes_updater.save_recipes(request, recipes)
            log.info(f'recipes module {module_name} finished with result {task_result}')
            return task_result
        except Exception as e:
            print(f'Error while processing {module_name}:')
            print(e)
            # print(traceback.format_tb(e.__traceback__))
            log.info(f'recipes module {module_name} finished with exception')
            return -1  # exception
    else:
        log.info(f'recipes module {module_name} finished with SOURCE_DISABLED')
        return -2  # source is disabled


async def collect_recipes(request):
    source_records = await db.get_all_sources(request.app['db'])
    source_names = [record['name'] for record in source_records]

    module_names = [name for _, name, _ in pkgutil.iter_modules(['scrape/scrapers'])]

    # asynchronously collect recipes for each module
    tasks = [collect_recipes_for_module(request, module_name, source_names) for module_name in module_names]
    try:
        await asyncio.wait(tasks)
    except Exception as e:
        print(e)


async def collect_recipes_for_module(request, module_name, source_names):
    module = importlib.import_module('.scrapers.' + module_name, 'scrape')
    recipes_updater = module.SourceUpdater()
    await recipes_updater._init(request)
    if recipes_updater.SOURCE_NAME in source_names:
        try:
            print(recipes_updater.SOURCE_NAME)
            await process_module(request, module_name)
        except Exception as e:
            print('error')
            traceback.print_tb(e.__traceback__)

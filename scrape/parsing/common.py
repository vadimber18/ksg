from ..parsing import bs
from ..parsing import selenium


async def parse_recipe_page(url, code, rules):
    engine = rules.get('engine')

    if engine == 'bs':
        return await bs.parse_recipe_page(url, code, rules)
    elif engine == 'selenium':
        return selenium.parse_recipe_page()


async def retrieve_recipes_links(rules):
    engine = rules.get('engine')

    if engine == 'bs':
        return await bs.retrieve_recipes_links(rules)
    elif engine == 'selenium':
        return selenium.retrieve_recipes_links()

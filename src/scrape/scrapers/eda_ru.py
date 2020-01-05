from scrape.scrape import RecipeUpdater
from ..helpers import og_image

from datetime import timedelta

import ast


def extract_ingredients(soup):
    ingredients_tags = soup.select('div.g-relative > div.ingredients-list > div.ingredients-list__content > p.ingredients-list__content-item')
    if ingredients_tags is not None:
        try:
            ingredients_tags = [ast.literal_eval(ingredients_tag['data-ingredient-object']) for ingredients_tag in ingredients_tags]
            return {ingredients_tag['name']: ingredients_tag['amount'] for ingredients_tag in ingredients_tags}
        except:
            return None
    else:
        return None


def extract_prep_time(soup):
    info_pad_items = soup.select('span.info-pad__item')
    if len(info_pad_items) > 1:
        try:
            prep_time = info_pad_items[1].select_one('span.info-text').text
            # dummy parse timedelta from string
            prep_time = prep_time.split()
            if len(prep_time) == 2:
                if 'час' in prep_time[1]:
                    return timedelta(hours=int(prep_time[0]))
                elif 'мин' in prep_time[1]:
                    return timedelta(minutes=int(prep_time[0]))
            elif len(prep_time) == 4:
                return timedelta(hours=int(prep_time[0]), minutes=int(prep_time[2]))
            else:
                return None
        except:
            return None
    else:
        return None


class SourceUpdater(RecipeUpdater):
    SOURCE_NAME = 'Eda ru'
    SOURCE_URL = 'https://eda.ru'


    PARSING_RULES = {
        'timeout': 4,
        'title': 'h1',
        'text': 'ul.recipe__steps > li > div > span',
        'main_image': og_image,
        'pub_date': None,
        'ingredients': extract_ingredients,
        'prep_time' : extract_prep_time
    }

    LINK_RETRIEVAL_RULES = {
        'links_selectors': ['div.tile-list__horizontal-tile > div.clearfix > div.horizontal-tile__content > h3 > a'],
        'links_pages': [
            {
                'url': '/recepty/supy',
                'category_code': 'SOUPS'
            },
            {
                'url': '/recepty/osnovnye-blyuda',
                'category_code': 'MAIN'
            },
            {
                'url': '/recepty/salaty',
                'category_code': 'SALADS'
            },
            {
                'url': '/recepty/vypechka-deserty',
                'category_code': 'DESSERTS'
            },
        ],
    }


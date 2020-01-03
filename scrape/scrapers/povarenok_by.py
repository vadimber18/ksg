from scrape.scrape import RecipeUpdater
import dateparser


def extract_datetime(soup):
    date_string = soup.select_one('div.item-preview__info_short')
    if date_string is not None:
        try:
            return dateparser.parse(' '.join(date_string.text.split()[2:5]))
        except:
            return None
    else:
        return None


def extract_ingredients(soup):
    ingredient_tags = soup.select('tr[itemprop="recipeIngredient"]') #> td')
    if ingredient_tags is not None:
        try:
            ingredients = []
            counts = []
            # otherwise there will be entries w/o count
            for ingredient_tag in ingredient_tags:
                ingr_count_tags = ingredient_tag.select('td')
                if len(ingr_count_tags) == 2:
                    ingredients.append(ingr_count_tags[0].text.strip())
                    counts.append(ingr_count_tags[1].text.strip())
            #ingredients = [tag.text.strip() for tag in ingredient_tags[0::2]]
            #counts = [tag.text.strip() for tag in ingredient_tags[1::2]]
            return dict(zip(ingredients, counts))
        except:
            return None
    else:
        return None


class SourceUpdater(RecipeUpdater):
    SOURCE_NAME = 'Povarenok by'
    SOURCE_URL = 'https://povarenok.by'
    SOURCE_DISABLED = False


    PARSING_RULES = {
        'timeout': 6,
        'title': 'div.item-preview > h1',
        'text': 'div[itemprop="recipeInstructions"]',
        'main_image': 'div.item-preview__image > a',
        'pub_date': extract_datetime,
        'ingredients': extract_ingredients,
        'prep_time': None
    }

    LINK_RETRIEVAL_RULES = {
        'links_selectors': ['div.item-preview > div.title > div > a'],
        'links_pages': [
            {
                'url': '/recepty/pervye-blyuda',
                'category_code': 'SOUPS'
            },
            {
                'url': '/recepty/vtorye-blyuda',
                'category_code': 'MAIN'
            },
            {
                'url': '/recepty/salaty',
                'category_code': 'SALADS'
            },
            {
                'url': '/recepty/deserty',
                'category_code': 'DESSERTS'
            },
            {
                'url': '/recepty/raznoe',
                'category_code': 'OTHER'
            },
        ],
    }


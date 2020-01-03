from scrape import helpers

from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

import re
import dateparser


def parse_title(soup, rules, fallback_value=None):
    parsing_rule = rules['title']

    title = fallback_value

    if callable(parsing_rule):  # callable returning title found in soup
        return parsing_rule(soup)

    elif type(parsing_rule) == str:  # css selector
        title = helpers.get_tag_text(soup, parsing_rule, fallback_value)

    elif type(parsing_rule) in (list, tuple):  # several css selectors
        title = helpers.get_text_of_first_encountered_tag(soup, parsing_rule, fallback_value)

    if title != fallback_value:
        title = title.strip()  # get rid of occasional spaces and \n's

    return title


# constants for parse_text(...)
FORBIDDEN_TEXT_FRAGMENTS = ['googletag', '0px;']
FORBIDDEN_TEXT_CLASSES = []
FORBIDDEN_TEXT_REGEXES = []


def parse_text(soup, rules, fallback_value=None):
    # get relevant settings
    parsing_rule = rules['text']
    auto_cleanup = rules['text_auto_cleanup']
    forbidden_fragments = rules['text_exclude_paragraphs_containing']
    forbidden_classes = rules['text_exclude_paragraphs_with_classes']
    forbidden_regexes = rules['text_finally_exclude_regexes']

    if auto_cleanup:
        forbidden_fragments += FORBIDDEN_TEXT_FRAGMENTS
        forbidden_classes += FORBIDDEN_TEXT_CLASSES
        forbidden_regexes += FORBIDDEN_TEXT_REGEXES

    # initialize text with fallback_value, proceed to selection cases
    text = fallback_value

    if callable(parsing_rule):  # callable returning text found in soup
        return parsing_rule(soup)

    elif type(parsing_rule) == str:  # convert one selector into a list of selectors
        parsing_rule = [parsing_rule]

    # it is important to have if here, not elif
    if type(parsing_rule) in (tuple, list):  # join all text found by the list of selectors
        paragraphs = []
        for selector in parsing_rule:
            for tag in soup.select(selector):
                # drop paragraphs with forbidden classes
                if any(tag.has_attr('class') and cls in tag.attrs['class'] for cls in forbidden_classes):
                    continue
                if any(tag.findChild(cls) is not None for cls in forbidden_classes):
                    continue

                paragraph = tag.text.strip()

                # drop paragraphs with forbidden text fragments
                if any(fragment in paragraph for fragment in forbidden_fragments):
                    continue

                paragraphs.append(paragraph)
        text = '\n'.join(paragraphs)

    # exclude forbidden regexes
    if text != fallback_value:
        for regex in forbidden_regexes:
            text = re.sub(regex, '', text)

    text = text.strip()

    return text


def parse_main_image(soup, rules, fallback_value=None):
    parsing_rule = rules['main_image']

    # default to fallback value and then switch on cases
    main_image = fallback_value

    if callable(parsing_rule):  # callable returning main image found in soup
        main_image = parsing_rule(soup)

    elif type(parsing_rule) == str:  # css selector
        main_image = helpers.get_first_tag_attribute(soup, parsing_rule, ('src', 'href'), fallback_value)

    return main_image


def parse_pub_date(soup, rules, fallback_value=None):
    parsing_rule = rules['pub_date']
    preprocessor = rules.get('pub_date_preprocessor')  # None if not in rules
    fmt = rules.get('pub_date_format')  # None if not in rules

    pub_date = fallback_value

    if callable(parsing_rule):  # callable returning publication date found in soup
        pub_date = parsing_rule(soup)

    elif type(parsing_rule) == str:
        tag = soup.select_one(parsing_rule)

        if tag is not None:
            if preprocessor is not None:  # preprocess tag
                if callable(preprocessor):
                    tag_text = preprocessor(tag)
                else:
                    raise Exception('Scraper configs only accept callable date preprocessors.')
            else:
                tag_text = tag.text.strip()

            if fmt is not None:
                pub_date = datetime.strptime(tag_text, fmt)
            else:
                pub_date = dateparser.parse(tag_text)

    return pub_date


def parse_ingredients(soup, rules, fallback_value=None):
    parsing_rule = rules['ingredients']

    ingredients = fallback_value

    if callable(parsing_rule):
        ingredients = parsing_rule(soup)

    return ingredients


def parse_prep_time(soup, rules, fallback_value=None):
    parsing_rule = rules['prep_time']

    prep_time = fallback_value

    if callable(parsing_rule):
        prep_time = parsing_rule(soup)

    return prep_time


async def parse_recipe_page(url, code, rules):
    page = await helpers.get_page(url, encoding=rules['encoding'], timeout=rules['timeout'])
    soup = BeautifulSoup(page, 'lxml')
    recipe_dict = dict()
    recipe_dict['title'] = parse_title(soup, rules)
    recipe_dict['text'] = parse_text(soup, rules)
    recipe_dict['main_image'] = parse_main_image(soup, rules, url)
    recipe_dict['pub_date'] = parse_pub_date(soup, rules)
    recipe_dict['ingredients'] = parse_ingredients(soup, rules)
    recipe_dict['prep_time'] = parse_prep_time(soup, rules)
    recipe_dict['url'] = url
    recipe_dict['category'] = code

    return recipe_dict


async def retrieve_recipes_links(rules):
    callback = rules.get('callback')
    pages = rules.get('links_pages')
    selectors = rules.get('links_selectors')
    timeout = rules.get('timeout')

    if callback is not None and callable(callback):
        return callback()
    else:
        if type(pages) not in (list, tuple):
            raise Exception('Links to recipe feed pages should be of iterable type.')
        if type(selectors) not in (list, tuple):
            raise Exception('Links selectors are incorrectly specified.')

        links = {}

        # do it synchronously otherwise it will be DDoS
        for links_page in pages:
            if type(links_page) == str:
                page = await helpers.get_page(links_page, timeout=timeout)
                soup = BeautifulSoup(page, 'lxml')
                for selector in selectors:
                    links.update({urljoin(links_page, a_tag['href']): None for a_tag in soup.select(selector)})
            elif type(links_page) == dict:
                page = await helpers.get_page(links_page['url'], timeout=timeout)
                soup = BeautifulSoup(page, 'lxml')
                for selector in selectors:
                    links.update({urljoin(links_page['url'], a_tag['href']): links_page['category_code'] for a_tag in
                                  soup.select(selector)})

        # asynchronously variation
        #tasks = [retrieve_page_links(links_page, timeout, selectors, links) for links_page in pages]
        #await asyncio.wait(tasks)
        return links


async def retrieve_page_links(links_page, timeout, selectors, links):
    if type(links_page) == str:
        page = await helpers.get_page(links_page, timeout=timeout)
        soup = BeautifulSoup(page, 'lxml')
        for selector in selectors:
            links.update({urljoin(links_page, a_tag['href']): None for a_tag in soup.select(selector)})
    elif type(links_page) == dict:
        page = await helpers.get_page(links_page['url'], timeout=timeout)
        soup = BeautifulSoup(page, 'lxml')
        for selector in selectors:
            links.update({urljoin(links_page['url'], a_tag['href']): links_page['category_code'] for a_tag in
                          soup.select(selector)})
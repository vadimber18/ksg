from datetime import timedelta
from user_agent import generate_user_agent

import dateparser
import aiohttp


async def get_page(url, encoding=None, max_retries=1, timeout=3, user_agent=None):

    if user_agent is None:
        user_agent = generate_user_agent()

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers={'User-Agent': user_agent}, timeout=timeout) as resp:
            assert resp.status == 200
            print(f'page downloaded at {url}')
            return await resp.text()


def get_tag_text(soup, selector, fallback_value=None):
    tag = soup.select_one(selector)
    if tag is None:
        return None
    else:
        return tag.text


def get_text_of_first_encountered_tag(soup, selectors, fallback_value=None):
    for selector in selectors:
        text = get_tag_text(soup, selector, fallback_value)
        if text != fallback_value:
            return text
    return fallback_value


def get_tag_attribute(soup, selector, key, fallback_value=None):
    tag = soup.select_one(selector)
    if tag is None:
        return fallback_value
    elif not tag.has_attr(key):
        return fallback_value
    else:
        return tag[key]


def get_first_tag_attribute(soup, selector, keys, fallback_value=None):
    tag = soup.select_one(selector)
    if tag is not None:
        for key in keys:
            if tag.has_attr(key):
                return tag.attrs[key]
    return fallback_value


def get_attribute_of_first_encountered_tag(soup, selectors: list, key, fallback_value=None):
    for selector in selectors:
        attribute = get_tag_attribute(soup, selector, key, fallback_value)
        if attribute != fallback_value:
            return attribute
    return fallback_value


def og_title(soup, fallback_value=None, strip_characters=None):
    selectors = ['meta[property="og:title"]', 'meta[name="og:title"]']
    title = get_attribute_of_first_encountered_tag(soup, selectors, 'content', fallback_value)
    if title != fallback_value:
        if strip_characters is not None:
            title.replace(strip_characters, '')
    return title


def og_image(soup, fallback_value=None):
    selectors = ['meta[property="og:image:secure_url"]', 'meta[name="og:image:secure_url"]',
                 'meta[property="og:image"]', 'meta[name="og:image"]']
    return get_attribute_of_first_encountered_tag(soup, selectors, 'content', fallback_value)



OG_DATETIME_FMT_WITH_SECONDS = '%Y-%m-%dT%H:%M:%S'
OG_DATETIME_FMT_WITHOUT_SECONDS = '%Y-%m-%dT%H:%M'


def og_datetime_no_offset(soup, fallback_value=None):
    og_pub_time = soup.select_one('meta[property="article:published_time"]')
    if og_pub_time:
        datetime_str = og_pub_time['content'][:-6]

        return dateparser.parse(datetime_str)
    else:
        return fallback_value


def og_datetime_offset(offset_h=0, offset_m=0):
    return lambda soup: og_datetime_no_offset(soup) - timedelta(hours=offset_h, minutes=offset_m)
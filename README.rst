KSG-aiohttp
===========

Project is mainly educational. Most of things are done in a simple way.

Apps
---------

recipes
^^^^^^^

* contains 7 API handlers (`register`, `login`, `recipes`, `favored`, `recipe_detail`, `vote_recipe`, `comment_recipe`) and 3 jinja-powered pages (recipes, recipe_detail, collect)
* API: logged in users can vote for recipe and comment it. for each recipe object they've got `liked` field - means if current user liked this recipe. liked recipes can be obtained by favored endpoint.
* non-API:  in `recipe_detail` non-api handler users can discuss recipe in chat using websockets. `collect` handler uses scrape app.

scrape
^^^^^

This app is parsing modules described in `scrape/scrapers` and collect recipes from them. app uses mainly bs4.

Features
---------

auth_middleware
^^^^^^^^^^^^^^^

Each API handler processed by `auth_middleware` - simple jwt token implementation described in `middlewares.py`

aiohttp-admin
^^^^^^^^^^^^^

    %gif%

swagger
^^^^^^^

Each API endpoint described. loads from .json file.

docker
^^^^^^

There are two docker configurations - local.yml and production.yml. production one uses caddy web-server to serve static and main app


tests
^^^^^

App contains tests for API handlers using aiohttp-pytest. some of them load data from json-fixtures

Installation
------------

* `docker-compose -f production.yml build`
* `docker-compose -f production.yml up`
* to run tests: `docker-compose -f local.yml run aio pytest tests`
* go to `127.0.0.1/collect` to collect recipes
* `swagger` available on `127.0.0.1:8000`, but you can always use Insomnia or such thing to test API.
* `aiohttp-admin` available on `127.0.0.1/admin` `user:admin password:admin_pass`
* main non-api available views on `127.0.0.1`
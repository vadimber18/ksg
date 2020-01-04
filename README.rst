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

* `make build_prod`
* `make run_prod`
* to run tests: `make test`
* go to `127.0.0.1/collect` to collect recipes
* `swagger` available on `127.0.0.1:8000`, but you can always use Insomnia or such thing to test API.
* `aiohttp-admin` available on `127.0.0.1/admin` `user:admin password:admin_pass`
* main non-api available views on `127.0.0.1`

TODO list
------------
* cleanup
* aiologstash logs (w elk image)
* custom exceptions
* raw sql
* several responses (w data/files?)
* permissions (superusers?)
* gitlab cron tests (mocks?)
* redis (?)
* files (upload commentary photos)
* cron-tasks (send weekly top for fav user activity categories)
* load-balance
* improve swagger (nullable, inher etc)
* insomnia config
* host
* git things
* cleanup
* collect for all users API - ordinary user can collect every N hours (last time stored in redis?) and superuser can do it always


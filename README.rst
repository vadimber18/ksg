KSG-aiohttp
===========

KSG stands for ``kura s grechey`` - it is a recipes search engine that aggregates recipes from several sources. Project is mainly educational, most of things are done in a simple way.

Apps
---------

recipes
^^^^^^^

* Contains 7 API handlers (``register``, ``login``, ``current_user``, ``recipes``, ``favored``, ``recipe_detail``, ``vote_recipe``, ``comment_recipe``, ``collect``, ``userpic_upload``) and 3 jinja-powered pages (``recipes``, ``recipe_detail``, ``collect``)
* API: authorized users can vote for recipe and comment it. Each recipe object got ``liked`` field - means if current user liked this recipe. Liked recipes can be obtained by favored endpoint.
* Non-API views:  in ``recipe_detail`` non-api handler users can discuss recipe in chat using websockets. ``collect`` handler uses scrape app.

scrape
^^^^^

This app is parsing modules described in ``scrape/scrapers`` and collect recipes from them. App uses mainly bs4.

Features
---------

docker
^^^^^^

There are three docker-compose configurations - local.yml, production.yml and test.yml. Production one uses caddy web-server to serve static and main app. Also, production build contains ELK-container.

auth_middleware
^^^^^^^^^^^^^^^

Each API handler processed by ``auth_middleware`` - simple jwt token implementation described in ``middlewares.py``

aiohttp-admin
^^^^^^^^^^^^^

.. image:: https://user-images.githubusercontent.com/17683944/74587363-80d7bb80-5002-11ea-8615-e2caa5150466.gif 

swagger
^^^^^^^

Each API endpoint described. Loads from .json file and can be accessed on 8001 port

tests
^^^^^

App contains tests for API handlers using aiohttp-pytest. Some of them load data from json-fixtures, it also contains coverage report

elk
^^^^^

ELK is used to log and deal with non-standard exceptions. Kibana is available on 5601 port (on production build only). Likely, you'll have to run ``sudo sysctl -w vm.max_map_count=262144`` so that the elk container start normally


Installation
------------

* ``make build_prod && make run_prod`` for production or ``make build && make run`` for local build
* to run tests: ``make test``
* you can collect recipes on ``%host%/collect``
* ``swagger`` available on ``%host%:8000``, but you can always use Insomnia or such thing to test API. Repository contains Insomnia config for all the API-endpoints
* ``aiohttp-admin`` available on ``%host%/admin`` ``user:admin password:admin_pass``
* main non-api available views on ``%host%``

TODO list
------------
* git things
* gitlab cron tests (mocks?)
* host


* fileresponse - .txt description?
* cron-tasks (emails?) (send weekly top for fav user activity categories)
* load-balance (?)


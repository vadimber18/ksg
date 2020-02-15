build:
	docker-compose -f local.yml build
run:
	docker-compose -f local.yml up
build_prod:
	docker-compose -f production.yml build
run_prod:
	docker-compose -f production.yml up
build_test:
	docker-compose -f test.yml build
test:
	docker-compose -f test.yml run aio /bin/bash -c "coverage run -m pytest tests; coverage report"

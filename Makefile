build:
	docker-compose -f local.yml build
run:
	docker-compose -f local.yml up
test:
	docker-compose -f local.yml run aio pytest tests
build_prod:
	docker-compose -f production.yml build
run_prod:
	docker-compose -f production.yml up

build:
	docker-compose -f production.yml build
test:
	docker-compose -f local.yml run aio pytest tests
run:
	docker-compose -f local.yml up
run_prod:
	docker-compose -f production.yml up

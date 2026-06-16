.PHONY: compose-up compose-down logs test-compose

compose-up:
	docker compose up --build -d

compose-down:
	docker compose down -v

logs:
	docker compose logs -f

test-compose:
	newman run postman/collections/b5_analytics_test.json -e postman/environments/local.json


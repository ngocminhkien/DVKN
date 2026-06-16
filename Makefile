.PHONY: compose-up compose-down logs test-compose

compose-up:
	docker compose up --build -d

compose-down:
	docker compose down -v

logs:
	docker compose logs -f

test-compose:
	newman run postman/collections/analytics_service.json -e postman/environments/local.json

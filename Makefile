.PHONY: dev stop test lint migrate migrate-create logs clean build prod

dev:
	docker compose up --build -d

stop:
	docker compose down

test:
	docker compose exec gateway-api pytest tests/ -v

lint:
	docker compose exec gateway-api ruff check app/

migrate:
	docker compose exec gateway-api alembic upgrade head

migrate-create:
	@read -p "Migration message: " msg; \
	docker compose exec gateway-api alembic revision --autogenerate -m "$$msg"

logs:
	docker compose logs -f

clean:
	docker compose down -v --remove-orphans

build:
	docker compose build

prod:
	docker compose -f docker-compose.prod.yml up --build -d

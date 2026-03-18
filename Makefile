.PHONY: up down build logs shell-backend migrate seed test lint

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

shell-backend:
	docker compose exec backend bash

migrate:
	docker compose exec backend alembic upgrade head

migrate-create:
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

seed:
	docker compose exec backend python scripts/seed_data.py

test:
	docker compose exec backend pytest

lint:
	docker compose exec backend ruff check app/

format:
	docker compose exec backend ruff format app/

restart:
	docker compose restart backend frontend

db-shell:
	docker compose exec postgres psql -U gramscout -d gramscout

redis-shell:
	docker compose exec redis redis-cli

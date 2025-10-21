.PHONY: help build up down restart logs migrate shell clean dev-up

help:
	@echo "=== Docker команды ==="
	@echo "  make build          - Собрать Docker образы"
	@echo "  make up             - Запустить все сервисы в Docker"
	@echo "  make down           - Остановить все сервисы"
	@echo "  make restart        - Перезапустить сервисы"
	@echo "  make logs           - Показать логи приложения"
	@echo "  make logs-all       - Показать все логи"
	@echo "  make ps             - Статус контейнеров"
	@echo ""
	@echo "=== Работа с БД ==="
	@echo "  make migrate        - Применить миграции"
	@echo "  make migrate-create - Создать миграцию"
	@echo "  make shell-db       - PostgreSQL консоль"
	@echo "  make shell-redis    - Redis консоль"
	@echo ""
	@echo "=== Разработка ==="
	@echo "  make shell          - Shell в контейнере приложения"
	@echo "  make dev-up         - Только БД+Redis для локальной разработки"
	@echo "  make dev-down       - Остановить БД+Redis"
	@echo "  make clean          - Удалить все контейнеры и volumes"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Приложение запущено на http://localhost:8000"

down:
	docker-compose down

restart:
	docker-compose restart

ps:
	docker-compose ps

logs:
	docker-compose logs -f app

logs-all:
	docker-compose logs -f

migrate:
	docker-compose exec app alembic upgrade head

migrate-create:
	@read -p "Название миграции: " msg; \
	docker-compose exec app alembic revision --autogenerate -m "$$msg"

migrate-downgrade:
	docker-compose exec app alembic downgrade -1

shell:
	docker-compose exec app /bin/bash

shell-db:
	docker-compose exec db psql -U soccer -d generate_pictures

shell-redis:
	docker-compose exec redis redis-cli

dev-up:
	docker-compose up db redis -d
	@echo "PostgreSQL: localhost:5432"
	@echo "Redis: localhost:6379"

dev-down:
	docker-compose stop db redis

clean:
	docker-compose down -v
	docker system prune -f

test:
	docker-compose exec app pytest

test-local:
	pytest
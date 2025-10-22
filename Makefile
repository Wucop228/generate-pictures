.PHONY: help build build-gpu up up-gpu down down-gpu restart logs migrate shell clean dev-up detect-gpu

help:
	@echo "=== Docker команды ==="
	@echo "  make build          - Собрать Docker образы"
	@echo "  make build-gpu      - Собрать Docker образы с GPU поддержкой"
	@echo "  make up             - Запустить все сервисы в Docker"
	@echo "  make up-gpu         - Запустить все сервисы в Docker с GPU поддержкой"
	@echo "  make down           - Остановить все сервисы"
	@echo "  make down-gpu       - Остановить все сервисы с GPU поддержкой"
	@echo "  make restart        - Перезапустить сервисы"
	@echo "  make restart-worker - Перезапустить Celery воркер"
	@echo "  make detect-gpu     - Автоопределение GPU (в powershell не работает)"
	@echo "  make logs           - Показать логи приложения"
	@echo "  make logs-worker    - Показать логи Celery воркера"
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
	@echo "  make shell-worker   - Shell в контейнере Celery воркера"
	@echo "  make dev-up         - Только БД+Redis для локальной разработки"
	@echo "  make dev-down       - Остановить БД+Redis"
	@echo "  make clean          - Удалить все контейнеры и volumes"

build:
	docker-compose build

build-gpu:
	docker-compose -f docker-compose.yml -f docker-compose.gpu.yml build

up:
	docker-compose up -d
	@echo "Приложение запущено на http://localhost:8000"
	@echo "Celery воркер: 3 процесса (CPU режим)"

up-gpu:
	docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
	@echo "Приложение запущено на http://localhost:8000 (GPU режим)"
	@echo "Celery воркер: 3 процесса (CUDA режим)"

down:
	docker-compose down

down-gpu:
	docker-compose -f docker-compose.yml -f docker-compose.gpu.yml down

detect-gpu:
	@if command -v nvidia-smi > /dev/null 2>&1; then \
		echo "GPU обнаружена, запуск в GPU режиме..."; \
		$(MAKE) build-gpu up-gpu; \
	else \
		echo "GPU не найдена, запуск в CPU режиме..."; \
		$(MAKE) build up; \
	fi

restart:
	docker-compose restart

restart-worker:
	docker-compose restart celery_worker
	@echo "Celery воркер перезапущен"

ps:
	docker-compose ps

logs:
	docker-compose logs -f app

logs-worker:
	docker-compose logs -f celery_worker

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

shell-worker:
	docker-compose exec celery_worker /bin/bash

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
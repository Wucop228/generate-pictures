.PHONY: help build-cpu build-gpu up up-gpu down logs-worker clean

help:
	@echo "Сборка образов:"
	@echo "  make build-cpu      - Собрать CPU образы"
	@echo "  make build-gpu      - Собрать GPU образы"
	@echo ""
	@echo "▶Запуск:"
	@echo "  make up             - Запустить CPU режим"
	@echo "  make up-gpu         - Запустить GPU режим"
	@echo ""
	@echo "Остановка:"
	@echo "  make down           - Остановить все сервисы"
	@echo "  make restart-worker - Перезапустить Celery воркер"
	@echo ""
	@echo "Логи и статус:"
	@echo "  make logs-worker    - Логи Celery воркера"
	@echo "  make logs-app       - Логи FastAPI приложения"
	@echo "  make ps             - Статус контейнеров"
	@echo ""
	@echo "Очистка:"
	@echo "  make clean          - Удалить всё (образы, volumes, контейнеры)"

build-cpu:
	docker-compose build

build-gpu:
	docker-compose -f docker-compose.yml -f docker-compose.gpu.yml build celery_worker

up:
	docker-compose up -d
	@echo ""
	@echo "Приложение запущено!"
	@echo "   FastAPI: http://localhost:8000"
	@echo "   Celery: 1 воркер (CPU, solo pool)"

up-gpu:
	docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
	@echo ""
	@echo "Приложение запущено!"
	@echo "   FastAPI: http://localhost:8000"
	@echo "   Celery: 1 воркер (CUDA, solo pool)"

down:
	docker-compose -f docker-compose.yml -f docker-compose.gpu.yml down

restart-worker:
	docker-compose restart celery_worker

logs-worker:
	docker-compose logs -f celery_worker

logs-app:
	docker-compose logs -f app

ps:
	docker-compose ps

clean:
	docker-compose -f docker-compose.yml -f docker-compose.gpu.yml down -v
	docker rmi generate_pictures_app:cpu generate_pictures_celery:cpu generate_pictures_celery:gpu 2>/dev/null || true
	docker system prune -f

migrate:
	docker-compose exec app alembic upgrade head

migrate-create:
	docker-compose exec app alembic revision --autogenerate -m "$$msg"

shell-app:
	docker-compose exec app /bin/bash

shell-worker:
	docker-compose exec celery_worker /bin/bash

shell-db:
	docker-compose exec db psql -U ${DB_USER} -d ${DB_NAME}

shell-redis:
	docker-compose exec redis redis-cli

dev-up:
	docker-compose up db redis -d
	@echo "PostgreSQL: localhost:5432"
	@echo "Redis: localhost:6379"

dev-down:
	docker-compose stop db redis
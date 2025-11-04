# Generate Pictures (FastAPI)

AI‑сервис для генерации изображений: FastAPI + Celery + Redis + Postgresql + S3 (Yandex Object Storage). Тесты на `pytest` с моками (`fakeredis`, `moto`).

## Описание проекта
Сервис представляет собой api для генерации картинки с помощью локально ИИ модели
- Регистрация пользователя и смена пароля.
- Аутентификация по JWT (**cookie** `access_token`, HttpOnly, 1 час).
- Хранение данных: PostgreSQL (пользователи/картинки), S3 (файлы изображений).
- Фоновая генерация изображений (CPU/GPU) через **Celery** (брокер **Redis**).
- Получение ссылки на скачивание через **presigned URL** (по умолчанию ~1 час).
- Полный набор тестов (unit/integration/e2e).
- Docker и CI (GitHub Actions).

## Стек
- **Язык:** Python 3.11
- **Фреймворк:** Fastapi
- **Хранилище:** Postgresql + SQLAlchemy , S3 (через `aioboto3`)
- **Очереди:** Celery
- **Брокер:** Redis
- **Миграции:** Alembic
- **ML:** локальная модель (папка `ai-image-generator`)
- **Тесты:** pytest (+ `fakeredis`, `moto`)

---

## Быстрый старт

1) Клонирование и окружение
```bash
git clone https://github.com/Wucop228/generate-pictures.git
cd generate-pictures
cp .env.example .env
```

2) Сборка и запуск
```bash
#если генерировать картинку с помощью cpu
make build-cpu
make up
```

```bash
#если с помощью gpu
make build-cpu
make build-gpu
make up-gpu
```

Приложение запущено тут: <http://localhost:8000>  
Документация: <http://localhost:8000/docs>

Логи воркера:
```bash
make logs-worker
```

Остановка:
```bash
make down
```

---

## Переменное окружение

Пример `.env.example`:
```env
DB_USER=db_user
DB_PASSWORD=db_password
DB_NAME=db_name
DB_PORT=5432
DB_HOST=localhost

SECRET_KEY=##################
ALGORITHM=HS256

REDIS_URL=redis://localhost:6379

S3_KEY_ID=...
S3_SECRET_KEY=...
S3_BUCKET_NAME=...

FORCE_DEVICE=cpu

LOG_LEVEL=DEBUG
```

---

## Тесты

### Локально
```bash
make test-host         # тесты
make test-host-cov     # покрытие тестами
```

### В Docker
```bash
make test              # тесты
make test-cov          # покрытие тестами
```

---

## Makefile — основные команды
```bash
make build-cpu   # сборка образа (если gpu использовать build-gpu)
make up          # поднять стек (если gpu использовать up-gpu)
make down        # остановить стек
make logs-worker # логи Celery worker
make logs-app    # логи приложения
```

---

## Структура проекта
```
├── Dockerfile.cpu                           # Dockerfile для cpu
├── Dockerfile.gpu                           # Dockerfile для gpu
├── Makefile                                 # Makefile
├── README.md
├── alembic.ini
├── alembic_migrations                       # миграции
│   ├── __init__.py
│   ├── env.py
│   └── versions                             # версии
│       ├── 2025_10_10_0934-87dcdcadab5b_create_table_users.py
│       ├── 2025_10_29_0433-71e396003e69_shim_restore_deleted_revision.py
│       ├── 2025_10_29_0441-2c4a6633891d_create_pictures.py
│       └── __init__.py
├── app
│   ├── __init__.py
│   ├── api                                  # хенделры
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── pictures.py
│   │   └── users.py
│   ├── auth                                 # аутентификация/регистрация
│   │   ├── __init__.py
│   │   ├── dao.py                           # работа с бд для auth
│   │   ├── dependencies.py                  # зависимости
│   │   ├── models.py                        # модели auth
│   │   ├── schemas.py                       # схемы для работы с auth
│   │   ├── service.py                       # бизнес-логика auth
│   │   └── utils.py                         # вспомогательные функции
│   ├── core                                 # общие компоненты
│   │   ├── __init__.py
│   │   ├── base_dao.py                      # запросы в бд
│   │   ├── config.py                        # конфиг
│   │   ├── database.py                      # настройка бд
│   │   └── log_setup.py                     # настройка логирования
│   ├── main.py
│   ├── middleware                           # мидлвары
│   │   ├── __init__.py
│   │   ├── auth.py                          # авторизация пользователя
│   │   └── request_id.py                    # request_id каждого запроса
│   ├── migration
│   ├── pictures                             # работа с pictures
│   │   ├── __init__.py
│   │   ├── celery_app.py                    # фоновые задачи для генерации pictures
│   │   ├── dao.py                           # работа с бд для pictures
│   │   ├── models.py                        # модели pictures
│   │   ├── redis_manager.py                 # работа с redis
│   │   ├── s3_manager.py                    # работа с S3
│   │   ├── schemas.py                       # схемы для работы с pictures
│   │   ├── service.py                       # бизнес-логика pictures
│   │   └── tasks.py                         # работа с ИИ моделью для генерации картинки
│   └── users                                # работа с users
│       ├── __init__.py
│       ├── dao.py                           # работа с бд для users
│       ├── models.py                        # модели users
│       ├── schemas.py                       # схемы для работы с users
│       └── service.py                       # бизнес-логика users
├── docker-compose.gpu.yml                   # docker-compose для gpu
├── docker-compose.yml                       # docker-compose для cpu
├── pytest.ini
├── requirements.txt                         # зависимости
└── tests
    ├── __init__.py
    ├── conftest.py                          # настройка для тестов 
    ├── e2e                                  # e2e тесты
    │   ├── __init__.py
    │   ├── test_auth.py
    │   ├── test_pictures.py
    │   └── test_users.py
    ├── integration                          # интеграционные тесты
    │   ├── __init__.py
    │   ├── test_dao_db.py
    │   ├── test_redis_manager.py
    │   └── test_s3_manager.py
    └── unit                                 # юнит тесты
        ├── __init__.py
        ├── test_auth_jwt_claims.py
        ├── test_auth_utils.py
        ├── test_config.py
        ├── test_middleware_request_id.py
        └── test_schemas.py

../ai-image-generator/                       # локальная ML‑модель
```

---

## Эндпоинты
**Auth**
- `POST /auth/login` — вход, ставит cookie `access_token` (HttpOnly).
- `POST /auth/logout` — выход, очищает cookie.

**Users**
- `POST /users/register` — регистрация.
- `POST /users/change-password` — смена пароля.
- `GET  /users/me` — получить профиль **(защищён AuthMiddleware)**.

**Pictures** *(все эндпоинты защищены AuthMiddleware)*
- `POST /pictures/generate` — создать задачу генерации. Возвращает `task_id` и начальный `status`.
- `GET  /pictures/status?task_id=...` — статус задачи.
- `GET  /pictures/{task_id}` — информация по картинке.
- `GET  /pictures` — список картинок пользователя.
- `GET  /pictures/download/{task_id}` — presigned URL для скачивания.
- `DELETE /pictures/{task_id}` — удалить запись/файл.

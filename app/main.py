from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.middleware.auth import AuthMiddleware

from app.api.users import router as users_router
from app.api.auth import router as auth_router
from app.api.pictures import router as pictures_router
from app.api.pictures import startup_pictures, shutdown_pictures
from app.pictures.redis_manager import redis_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Запуск приложения...")
    try:
        await redis_manager.connect()
    except Exception as e:
        print(f"Ошибка подключения к Redis: {e}")
        raise

    startup_pictures()

    print("Приложение успешно запущено")

    yield

    print("Остановка приложения...")

    shutdown_pictures()

    await redis_manager.disconnect()

    print("Приложение остановлено")

app = FastAPI(lifespan=lifespan)

app.add_middleware(AuthMiddleware)

app.include_router(users_router)
app.include_router(auth_router)
app.include_router(pictures_router)
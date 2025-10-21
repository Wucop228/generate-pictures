from fastapi import FastAPI
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

from app.middleware.auth import AuthMiddleware
from app.api.users import router as users_router
from app.api.auth import router as auth_router
from app.api.pictures import router as pictures_router
from app.pictures.redis_manager import redis_manager
from app.core.config import MAX_WORKERS


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Запуск приложения...")

    app.state.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
    print(f"✅ ThreadPoolExecutor создан (workers: {MAX_WORKERS})")

    await redis_manager.connect()
    print("✅ Redis подключен")

    yield

    print("🛑 Остановка приложения...")

    app.state.executor.shutdown(wait=True)
    print("✅ ThreadPoolExecutor остановлен")

    await redis_manager.disconnect()
    print("✅ Redis отключен")

app = FastAPI(lifespan=lifespan)

app.add_middleware(AuthMiddleware)

app.include_router(users_router)
app.include_router(auth_router)
app.include_router(pictures_router)
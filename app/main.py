import logging

from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.log_setup import setup_logging
from app.middleware.auth import AuthMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.api.users import router as users_router
from app.api.auth import router as auth_router
from app.api.pictures import router as pictures_router
from app.pictures.redis_manager import redis_manager

setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск приложения...")
    await redis_manager.connect()
    logger.info("Redis подключен")
    try:
        yield
    finally:
        logger.info("Остановка приложения...")
        await redis_manager.disconnect()
        logger.info("Redis отключен")

app = FastAPI(lifespan=lifespan)

app.add_middleware(RequestIdMiddleware)
app.add_middleware(AuthMiddleware)

app.include_router(users_router)
app.include_router(auth_router)
app.include_router(pictures_router)
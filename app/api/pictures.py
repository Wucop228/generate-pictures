import os
import time
import uuid
import logging
from typing import List

from fastapi import APIRouter, Request, status, HTTPException, Response
from sqlalchemy import and_

from app.pictures.schemas import PictureCreate, TaskInfo, TaskStatus, PictureCreateResponse
from app.pictures.redis_manager import redis_manager
from app.pictures.s3_manager import s3_manager
from app.pictures.tasks import generate_picture_task
from app.pictures.dao import PicturesDAO
from app.pictures.models import Picture
from app.core.config import GENERATED_PICTURES_DIR

router = APIRouter(prefix="/pictures", tags=["pictures"])
logger = logging.getLogger("app.api.pictures")

@router.post("/generate", response_model=PictureCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_picture(request: Request, picture: PictureCreate):
    user_id = request.state.user_id

    task_id = str(uuid.uuid4())
    timestamp_ms = int(time.time() * 1000)
    filename = f"picture_{user_id}_{timestamp_ms}.png"
    path_to_picture = os.path.join(GENERATED_PICTURES_DIR, filename)

    logger.info(
        "Создание задачи генерации: task_id=%s user_id=%s prompt_len=%s",
        task_id, user_id, len(picture.prompt) if picture and picture.prompt else 0
    )

    task = TaskInfo(
        task_id=task_id,
        user_id=user_id,
        prompt=picture.prompt,
        status=TaskStatus.PENDING,
        filename=filename,
        filepath=path_to_picture,
        created_at=timestamp_ms,
        num_inference_steps=picture.num_inference_steps,
        guidance_scale=picture.guidance_scale
    )

    logger.debug("Сохраняю задачу в Redis: task_id=%s", task_id)
    try:
        await redis_manager.save_task(task)
    except Exception:
        logger.exception("Сбой записи задачи в Redis: task_id=%s", task_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка сохранения задачи Redis"
        )

    logger.debug("Сохраняю задачу в БД: task_id=%s", task_id)
    try:
        await PicturesDAO.add(
            user_id=user_id,
            task_id=task_id,
            prompt=picture.prompt,
            status=TaskStatus.PENDING,
            filename=filename,
        )
    except Exception:
        logger.exception("Сбой сохранения задачи в БД: task_id=%s", task_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось добавить задачу в БД"
        )
    logger.debug("Задача успешно сохранена в БД: task_id=%s", task_id)

    logger.debug("Отправляю задачу в очередь: task_id=%s", task_id)
    try:
        generate_picture_task.delay(task_id)
    except Exception:
        logger.exception("Сбой постановки задачи в очередь: task_id=%s", task_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось отправить задачу в очередь"
        )

    logger.info("Задача принята: task_id=%s", task_id)
    return PictureCreateResponse(
        success=True,
        message="Запрос на создание картинки успешно создан",
        task_id=task_id,
        status=TaskStatus.PENDING
    )

@router.get("/status", response_model=TaskStatus, status_code=status.HTTP_200_OK)
async def get_picture_status(request: Request, task_id: str):
    user_id = request.state.user_id
    logger.debug("Статус задачи: запрос task_id=%s user_id=%s", task_id, user_id)

    try:
        picture = await PicturesDAO.find_one_or_none_by_filter(
            and_(Picture.task_id == task_id, Picture.user_id == user_id)
        )
    except Exception:
        logger.exception("Сбой чтения картинки из БД: task_id=%s", task_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить картинку"
        )

    if picture is None:
        logger.warning("Картинка не найдена: task_id=%s user_id=%s", task_id, user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Картинка не найдена",
        )

    logger.info("Статус задачи: task_id=%s status=%s", task_id, picture.status)
    return picture.status

@router.get("/{task_id}", response_model=TaskInfo, status_code=status.HTTP_200_OK)
async def get_picture(request: Request, task_id: str):
    user_id = request.state.user_id
    logger.debug("Получение картинки: запрос task_id=%s user_id=%s", task_id, user_id)

    try:
        picture = await PicturesDAO.find_one_or_none_by_filter(
            and_(Picture.task_id == task_id, Picture.user_id == user_id)
        )
    except Exception:
        logger.exception("Сбой чтения картинки из БД: task_id=%s", task_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить картинку"
        )

    if picture is None:
        logger.warning("Картинка не найдена: task_id=%s user_id=%s", task_id, user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Картинка не найдена",
        )

    logger.info("Картинка получена: task_id=%s user_id=%s prompt_len=%s", task_id, user_id, len(picture.prompt))
    return picture

@router.get("", response_model=List[TaskInfo], status_code=status.HTTP_200_OK)
async def get_pictures(request: Request):
    user_id = request.state.user_id
    logger.debug("Получение картинок: запрос user_id=%s", user_id)

    try:
        pictures = await PicturesDAO.find_all(user_id=user_id)
        pictures.sort(key=lambda p: p.created_at or 0, reverse=True)
    except Exception:
        logger.exception("Сбой чтения картинок из БД: user_id=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить картинки"
        )

    logger.info("Картинки получены: user_id=%s count=%s", user_id, len(pictures))
    return pictures

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_picture(request: Request, task_id: str):
    user_id = request.state.user_id
    logger.info("Удаление картинки: task_id=%s user_id=%s", task_id, user_id)

    try:
        picture = await PicturesDAO.find_one_or_none_by_filter(
            and_(Picture.task_id == task_id, Picture.user_id == user_id)
        )
    except Exception:
        logger.exception("Сбой чтения картинки из БД: task_id=%s", task_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить картинку"
        )

    if picture is None:
        logger.warning("Картинка не найдена: task_id=%s user_id=%s", task_id, user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Картинка не найдена",
        )

    try:
        if picture.s3_key:
            s3_manager.delete_file(picture.s3_key)
            logger.debug(
                "Успешно удалена картинка из S3: task_id=%s user_id=%s s3_key=%s",
                task_id, user_id, picture.s3_key
            )
        else:
            logger.debug(
                "Картинка не найдена в S3: task_id=%s user_id=%s s3_key=%s",
                task_id, user_id, picture.s3_key
            )
    except Exception:
        logger.exception(
            "Сбой удалении картинки в S3: task_id=%s user_id=%s s3_key=%s",
            task_id, user_id, picture.s3_key
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось удалить картинку из S3"
        )

    try:
        await PicturesDAO.delete(filter_by={"task_id": task_id})
    except Exception:
        logger.exception("Сбой удаления картинки в БД: task_id=%s user_id=%s", task_id, user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось удалить картинку из БД"
        )

    logger.info("Картинка удалена: task_id=%s user_id=%s", task_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/download/{task_id}", status_code=status.HTTP_200_OK)
async def download_picture(request: Request, task_id: str):
    user_id = request.state.user_id
    logger.debug("Получение ссылки на картинку: запрос task_id=%s user_id=%s", task_id, user_id)

    try:
        picture = await PicturesDAO.find_one_or_none_by_filter(
            and_(Picture.task_id == task_id, Picture.user_id == user_id)
        )
    except Exception:
        logger.exception("Сбой чтения картинки из БД: task_id=%s", task_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить картинку"
        )

    if picture is None:
        logger.warning("Картинка не найдена: task_id=%s user_id=%s", task_id, user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Картинка не найдена",
        )

    if not getattr(picture, "s3_key", None):
        logger.warning("Файл пока не доступен: task_id=%s user_id=%s", task_id, user_id)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Файл пока не доступен")

    url = ""
    try:
        url = s3_manager.get_presigned_url(picture.s3_key, expiration=3600)
    except Exception:
        logger.exception(
            "Сбой при получении ссылки из S3: task_id=%s user_id=%s s3_key=%s",
            task_id, user_id, picture.s3_key
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось получить ссылку")

    if not url:
        logger.error(
            "Пустой URL из S3: task_id=%s user_id=%s s3_key=%s",
            task_id, user_id, picture.s3_key
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось получить ссылку")

    logger.info("Ссылка получена: task_id=%s user_id=%s url_len=%s", task_id, user_id, len(url))
    return {"url": url}
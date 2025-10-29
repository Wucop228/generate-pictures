import os
import time
import uuid
from typing import List

from fastapi import APIRouter, Request, status, HTTPException
from sqlalchemy import and_

from app.pictures.schemas import PictureCreate, TaskInfo, TaskStatus, PictureCreateResponse
from app.pictures.redis_manager import redis_manager
from app.pictures.tasks import generate_picture_task
from app.pictures.dao import PicturesDAO
from app.pictures.models import Picture
from app.core.config import GENERATED_PICTURES_DIR

router = APIRouter(prefix="/pictures", tags=["pictures"])

@router.post("/generate", response_model=PictureCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_picture(request: Request, picture: PictureCreate):
    user_id = request.state.user_id

    task_id = str(uuid.uuid4())
    timestamp_ms = int(time.time() * 1000)
    filename = f"picture_{user_id}_{timestamp_ms}.png"
    path_to_picture = os.path.join(GENERATED_PICTURES_DIR, filename)

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

    await redis_manager.save_task(task)

    await PicturesDAO.add(
        user_id=user_id,
        task_id=task_id,
        prompt=picture.prompt,
        status=TaskStatus.PENDING,
        filename=filename,
    )

    generate_picture_task.delay(task_id)

    return PictureCreateResponse(
        success=True,
        message="Запрос на создание картинки успешно создан",
        task_id=task_id,
        status=TaskStatus.PENDING
    )

@router.get("/status", response_model=TaskStatus, status_code=status.HTTP_200_OK)
async def get_picture_status(request: Request, task_id: str):
    picture = await PicturesDAO.find_one_or_none_by_filter(
        and_(Picture.task_id == task_id, Picture.user_id == request.state.user_id)
    )

    if picture is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Картинка не найдена",
        )

    return picture.status

@router.get("/{task_id}", response_model=TaskInfo, status_code=status.HTTP_200_OK)
async def get_picture(request: Request, task_id: str):
    picture = await PicturesDAO.find_one_or_none_by_filter(
        and_(Picture.task_id == task_id, Picture.user_id == request.state.user_id)
    )

    if picture is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Картинка не найдена",
        )

    return picture

@router.get("", response_model=List[TaskInfo], status_code=status.HTTP_200_OK)
async def get_pictures(request: Request):
    user_id = request.state.user_id

    pictures = await PicturesDAO.find_all(user_id=user_id)
    pictures.sort(key=lambda p: p.created_at or 0, reverse=True)
    return pictures
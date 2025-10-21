import os
import time
import uuid

from fastapi import APIRouter, Request, status

from app.pictures.schemas import PictureCreate, TaskInfo, TaskStatus, PictureCreateResponse
from app.pictures.redis_manager import redis_manager
from app.pictures.service import run_generation
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

    executor = request.app.state.executor
    executor.submit(run_generation, task_id)

    return PictureCreateResponse(
        success=True,
        message="Запрос на создание картинки успешно создан",
        task_id=task_id,
        status=TaskStatus.PENDING
    )
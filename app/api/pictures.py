import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from fastapi import APIRouter, Request, status

from app.pictures.schemas import PictureCreate, TaskInfo, TaskStatus, PictureCreateResponse
from app.pictures.redis_manager import redis_manager
from app.pictures.service import run_generation
from app.core.config import GENERATED_PICTURES_DIR, MAX_WORKERS

router = APIRouter(prefix="/pictures", tags=["pictures"])

executor: Optional[ThreadPoolExecutor] = None

def startup_pictures():
    global executor
    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
    print(f"✅ Pictures: ThreadPoolExecutor создан ({MAX_WORKERS} workers)")

def shutdown_pictures():
    global executor
    if executor:
        print("🔄 Ожидание завершения активных задач...")
        executor.shutdown(wait=True, cancel_futures=False)
        print("✅ Pictures: ThreadPoolExecutor остановлен")

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

    executor.submit(run_generation, task_id)

    return PictureCreateResponse(
        success=True,
        message="Запрос на создание картинки успешно создан",
        task_id=task_id,
        status=TaskStatus.PENDING
    )
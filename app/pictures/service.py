import sys
from pathlib import Path

AI_GENERATOR_PATH = Path("/app/ai-image-generator")
if str(AI_GENERATOR_PATH) not in sys.path:
    sys.path.insert(0, str(AI_GENERATOR_PATH))

from generate import generate_picture

import asyncio

from app.pictures.redis_manager import redis_manager
from app.pictures.schemas import TaskStatus
from app.core.config import settings


def run_generation(task_id: str):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    thread_redis = redis_manager.get_sync_redis()

    try:
        task = loop.run_until_complete(redis_manager.get_task(task_id, redis_client=thread_redis))
        if not task:
            print(f"Задача {task_id} не найдена в Redis")
            return

        loop.run_until_complete(
            redis_manager.update_task_status(task_id, TaskStatus.PROCESSING, redis_client=thread_redis)
        )

        print(f"Начало генерации картинки для задачи {task_id}")
        print(f"Промпт: {task.prompt}")

        force_device = settings.FORCE_DEVICE

        generate_picture(
            prompt=task.prompt,
            path_to_picture=task.filepath,
            num_inference_steps=task.num_inference_steps,
            guidance_scale=task.guidance_scale,
            force_device=force_device
        )

        loop.run_until_complete(
            redis_manager.update_task_status(
                task_id,
                TaskStatus.COMPLETED,
                filename=task.filename,
                filepath=task.filepath,
                redis_client=thread_redis
            )
        )

        print(f"Картинка для задачи {task_id} готова!")
    except Exception as e:
        print(f"Ошибка при генерации картинки {task_id}: {e}")

        loop.run_until_complete(
            redis_manager.update_task_status(
                task_id,
                TaskStatus.FAILED,
                error=str(e),
                redis_client=thread_redis
            )
        )
    finally:
        loop.run_until_complete(thread_redis.close())
        loop.close()
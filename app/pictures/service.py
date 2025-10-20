import sys
import os
current_file_dir = os.path.dirname(os.path.abspath(__file__))
ai_image_generator_path = os.path.join(current_file_dir, '..', '..', '..', 'ai-image-generator')
ai_image_generator_path = os.path.normpath(ai_image_generator_path)
sys.path.insert(0, ai_image_generator_path)
from generate import generate_picture

import asyncio

from app.pictures.redis_manager import redis_manager
from app.pictures.schemas import TaskStatus


def run_generation(task_id: str):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)


    try:
        task = loop.run_until_complete(redis_manager.get_task(task_id))
        if not task:
            print(f"Задача {task_id} не найдена в Redis")
            return

        loop.run_until_complete(
            redis_manager.update_task_status(task_id, TaskStatus.PROCESSING)
        )

        print(f"Начало генерации картинки для задачи {task_id}")
        print(f"Промпт: {task.prompt}")

        generate_picture(
            task.prompt,
            task.filepath,
            num_inference_steps=task.num_inference_steps,
            guidance_scale=task.guidance_scale
        )

        loop.run_until_complete(
            redis_manager.update_task_status(
                task_id,
                TaskStatus.COMPLETED,
                filename=task.filename,
                filepath=task.filepath
            )
        )

        print(f"Картинка для задачи {task_id} готова!")
    except Exception as e:
        print(f"Ошибка при генерации картинки {task_id}: {e}")

        loop.run_until_complete(
            redis_manager.update_task_status(
                task_id,
                TaskStatus.FAILED,
                error=str(e)
            )
        )
    finally:
        loop.close()
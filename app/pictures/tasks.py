import torch
from pathlib import Path
import os

from diffusers import AutoPipelineForText2Image
from celery.signals import worker_process_init

from app.pictures.celery_app import celery_app
from app.pictures.redis_manager import RedisManager
from app.pictures.s3_manager import s3_manager
from app.pictures.schemas import TaskStatus
from app.pictures.dao import PicturesDAO
from app.core.config import settings

_model_cache = {}

def get_optimal_device(force_device: str = None):
    if force_device != "auto":
        print(f"Принудительное использование устройства: {force_device}")

        if force_device == "cuda":
            if not torch.cuda.is_available():
                print("CUDA недоступна! Переключение на CPU")
                device = "cpu"
                dtype = torch.float32
            else:
                device = "cuda"
                device_name = torch.cuda.get_device_name(0)
                dtype = torch.float16
                print(f"Используется NVIDIA GPU: {device_name}")

        elif force_device == "mps":
            if not (hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()):
                print("MPS недоступен! Переключение на CPU")
                device = "cpu"
                dtype = torch.float32
            else:
                device = "mps"
                dtype = torch.float32
                print(f"Используется Apple Metal (MPS)")

        elif force_device == "cpu":
            device = "cpu"
            dtype = torch.float32
            print(f"Используется CPU")

        else:
            print(f"Неизвестное устройство '{force_device}', использую авто-определение")
            force_device = "auto"

    if force_device == "auto":
        print("Автоматическое определение устройства...")

        if torch.cuda.is_available():
            device = "cuda"
            device_name = torch.cuda.get_device_name(0)
            dtype = torch.float16
            print(f"Используется NVIDIA GPU: {device_name}")
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device = "mps"
            dtype = torch.float32
            print(f"Используется Apple Metal (MPS)")
        else:
            device = "cpu"
            dtype = torch.float32
            print(f"Используется CPU (медленно)")

    return device, dtype


def load_model():
    print("Загрузка модели")

    device, dtype = get_optimal_device(settings.FORCE_DEVICE)

    model_path = Path("/app/ai-image-generator/models/dreamshaper-8")

    if not model_path.exists():
        raise FileNotFoundError(f"Модель не найдена: {model_path}")

    print(f"Путь к модели: {model_path}")
    print(f"Устройство: {device}")
    print(f"Тип данных: {dtype}")

    pipe = AutoPipelineForText2Image.from_pretrained(
        str(model_path),
        torch_dtype=dtype,
        local_files_only=True,
        safety_checker=None,
    )

    pipe = pipe.to(device)
    pipe.enable_attention_slicing()

    if device == "cuda":
        try:
            pipe.enable_xformers_memory_efficient_attention()
            print("xformers оптимизация включена")
        except Exception:
            print("xformers не установлен (опционально)")

    _model_cache["pipe"] = pipe
    _model_cache["device"] = device
    _model_cache["dtype"] = dtype

    print("Модель загружена")


@worker_process_init.connect
def init_worker_process(sender=None, **kwargs):
    print(f"Инициализация воркера (PID: {sender})")
    load_model()


def get_model():
    if "pipe" not in _model_cache:
        print("Модель не найдена в кеше")
        load_model()

    return _model_cache["pipe"], _model_cache["device"]


@celery_app.task(bind=True, name="generate_picture_task")
def generate_picture_task(self, task_id: str):
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    redis_mgr = RedisManager()
    redis_client = redis_mgr.get_sync_redis()

    try:
        task = loop.run_until_complete(
            redis_mgr.get_task(task_id, redis_client=redis_client)
        )

        if not task:
            print(f"Задача {task_id} не найдена в Redis")
            return

        loop.run_until_complete(
            redis_mgr.update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                redis_client=redis_client
            )
        )
        loop.run_until_complete(
            PicturesDAO.update(filter_by={"task_id": task_id}, status=TaskStatus.PROCESSING)
        )

        print(f"Генерация для задачи {task_id}")
        print(f"Промпт: {task.prompt}")
        print(f"Шаги: {task.num_inference_steps}")
        print(f"Guidance: {task.guidance_scale}")

        pipe, device = get_model()

        print("Генерация началась...")

        image = pipe(
            task.prompt,
            num_inference_steps=task.num_inference_steps,
            guidance_scale=task.guidance_scale,
        ).images[0]

        output_path = Path(task.filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(str(output_path))

        s3_key = f"users/{task.user_id}/{output_path.name}"
        if not s3_manager.upload_file(str(output_path), s3_key):
            raise RuntimeError("Не удалось загрузить файл в S3")

        try:
            os.remove(str(output_path))
            print(f"Файл {output_path} успешно удален")
        except FileNotFoundError:
            ...

        from os.path import basename
        loop.run_until_complete(
            PicturesDAO.update(
                filter_by={"task_id": task_id},
                status=TaskStatus.COMPLETED,
                filename=basename(task.filepath),
                s3_key=s3_key,
            )
        )

        print(f"Изображение сохранено: {task.filepath}")

        if device == "cuda":
            torch.cuda.empty_cache()
            print("🧹 Память GPU очищена")

        loop.run_until_complete(
            redis_mgr.update_task_status(
                task_id,
                TaskStatus.COMPLETED,
                filename=task.filename,
                filepath=task.filepath,
                redis_client=redis_client
            )
        )

        print(f"Задача {task_id} завершена успешно!")

    except Exception as e:
        print(f"Ошибка в задаче {task_id}: {e}")
        import traceback
        traceback.print_exc()

        loop.run_until_complete(
            redis_mgr.update_task_status(
                task_id,
                TaskStatus.FAILED,
                error=str(e),
                redis_client=redis_client
            )
        )
        loop.run_until_complete(
            PicturesDAO.update(filter_by={"task_id": task_id}, status=TaskStatus.FAILED, error=str(e))
        )
        raise

    finally:
        loop.run_until_complete(redis_client.close())
        loop.close()
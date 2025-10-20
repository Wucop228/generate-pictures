from typing import Optional

import redis.asyncio as redis

from app.core.config import settings, TASK_TTL
from app.pictures.schemas import TaskInfo, TaskStatus


class RedisManager:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None

    async def connect(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await self.redis.ping()
        print("Redis подключен")

    async def disconnect(self):
        if self.redis:
            await self.redis.close()
            print("Redis отключен")

    async def save_task(self, task: TaskInfo):
        key = f"task:{task.task_id}"
        value = task.model_dump_json()
        await self.redis.set(key, value, ex=TASK_TTL)

    async def get_task(self, task_id: str) -> Optional[TaskInfo]:
        key = f"task:{task_id}"
        data = await self.redis.get(key)
        if data:
            return TaskInfo.model_validate_json(data)
        return None

    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        filename: Optional[str] = None,
        filepath: Optional[str] = None,
        error: Optional[str] = None
    ):
        task = await self.get_task(task_id)
        if task:
            task.status = status
            if filename:
                task.filename = filename
            if filepath:
                task.filepath = filepath
            if error:
                task.error = error
            await self.save_task(task)

    async def get_user_task(self, user_id: int, limit: int = 10) -> list[TaskInfo]:
        pattern = "task:*"
        tasks = []

        async for key in self.redis.scan_iter(match=pattern, count=100):
            data = await self.redis.get(key)
            if data:
                task = TaskInfo.model_validate_json(data)
                if task.user_id == user_id:
                    task.append(task)
        tasks.sort(key=lambda x: x.created_at, reverse=True)
        return tasks[:limit]

redis_manager = RedisManager()
from typing import Optional

import redis.asyncio as redis

from app.core.config import settings, TASK_TTL
from app.pictures.schemas import TaskInfo, TaskStatus


class RedisManager:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.redis_url = settings.REDIS_URL

    async def connect(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await self.redis.ping()
        print("Redis подключен")

    async def disconnect(self):
        if self.redis:
            await self.redis.close()
            print("Redis отключен")

    def get_sync_redis(self):
        return redis.from_url(self.redis_url, decode_responses=True)

    async def save_task(self, task: TaskInfo, redis_client=None):
        client = redis_client if redis_client else self.redis
        key = f"task:{task.task_id}"
        value = task.model_dump_json()
        await client.setex(key, TASK_TTL, value)

    async def get_task(self, task_id: str, redis_client=None) -> Optional[TaskInfo]:
        client = redis_client if redis_client else self.redis
        key = f"task:{task_id}"
        data = await client.get(key)
        if data:
            return TaskInfo.model_validate_json(data)
        return None

    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        filename: Optional[str] = None,
        filepath: Optional[str] = None,
        error: Optional[str] = None,
        redis_client = None
    ):
        client = redis_client if redis_client else self.redis
        task = await self.get_task(task_id, redis_client=client)
        if task:
            task.status = status
            if filename:
                task.filename = filename
            if filepath:
                task.filepath = filepath
            if error:
                task.error = error
            await self.save_task(task, redis_client=client)

    async def get_user_task(self, user_id: int, limit: int = 10) -> list[TaskInfo]:
        pattern = "task:*"
        tasks = []

        async for key in self.redis.scan_iter(match=pattern, count=100):
            data = await self.redis.get(key)
            if data:
                task = TaskInfo.model_validate_json(data)
                if task.user_id == user_id:
                    tasks.append(task)
        tasks.sort(key=lambda x: x.created_at, reverse=True)
        return tasks[:limit]

redis_manager = RedisManager()
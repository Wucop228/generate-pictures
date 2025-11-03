import pytest
import fakeredis.aioredis
from app.pictures.schemas import TaskInfo, TaskStatus

pytestmark = pytest.mark.integration

@pytest.mark.asyncio
async def test_redis_manager_crud(monkeypatch):
    from app.pictures.redis_manager import RedisManager

    mgr = RedisManager()
    mgr.redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    t1 = TaskInfo(task_id="t1", user_id=1, prompt="p1", status=TaskStatus.PENDING,
                  filename=None, filepath=None, error=None, created_at=1761705121692,
                  num_inference_steps=15, guidance_scale=8.0)
    await mgr.save_task(t1)

    got = await mgr.get_task("t1")
    assert got and got.status == TaskStatus.PENDING

    await mgr.update_task_status("t1", TaskStatus.PROCESSING)
    got2 = await mgr.get_task("t1")
    assert got2.status == TaskStatus.PROCESSING

    t2 = TaskInfo(task_id="t2", user_id=2, prompt="p2", status=TaskStatus.PENDING,
                  filename=None, filepath=None, error=None, created_at=1761705121693,
                  num_inference_steps=15, guidance_scale=8.0)
    await mgr.save_task(t2)

    lst = await mgr.get_user_task(user_id=1, limit=10)
    assert len(lst) == 1 and lst[0].task_id == "t1"

@pytest.mark.asyncio
async def test_redis_get_unknown_returns_none():
    from app.pictures.redis_manager import RedisManager
    mgr = RedisManager()
    mgr.redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    assert await mgr.get_task("nope") is None

@pytest.mark.asyncio
async def test_redis_get_user_task_empty():
    from app.pictures.redis_manager import RedisManager
    mgr = RedisManager()
    mgr.redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    assert await mgr.get_user_task(1) == []
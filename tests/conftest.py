import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

@pytest.fixture
def fake_auth_middleware():
    class FakeAuthMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            request.state.user_id = 1
            request.state.is_authenticated = True
            return await call_next(request)
    return FakeAuthMiddleware

@pytest.fixture
def app_api(monkeypatch, fake_auth_middleware):
    import app.api.pictures as pictures_module
    from app.api.pictures import router as pictures_router
    from app.api.users import router as users_router
    from app.api.auth import router as auth_router
    from app.middleware.request_id import RequestIdMiddleware

    class _DummyTask:
        def delay(self, *args, **kwargs):
            self.last_call = (args, kwargs)
            return None
    monkeypatch.setattr(pictures_module, "generate_picture_task", _DummyTask(), raising=True)

    class _DummyRedis:
        def __init__(self):
            self._tasks = {}

        async def save_task(self, task, redis_client=None):
            self._tasks[task.task_id] = task
            return True

        async def set_task(self, task, redis_client=None):
            return await self.save_task(task, redis_client=redis_client)

        async def update_task_status(self, task_id, status, redis_client=None):
            t = self._tasks.get(task_id)
            if t:
                t.status = status
            return True

        async def get_user_task(self, user_id, limit=10, redis_client=None):
            tasks = [t for t in self._tasks.values() if t.user_id == user_id]
            return tasks[:limit]
    monkeypatch.setattr(pictures_module, "redis_manager", _DummyRedis(), raising=True)

    class _DummyS3:
        def get_presigned_url(self, key, expiration=3600):
            return f"https://example.com/{key}"

        def delete_file(self, key):
            return True
    monkeypatch.setattr(pictures_module, "s3_manager", _DummyS3(), raising=True)

    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(fake_auth_middleware)
    app.include_router(users_router)
    app.include_router(auth_router)
    app.include_router(pictures_router)
    return app

@pytest.fixture
def client(app_api):
    return TestClient(app_api)
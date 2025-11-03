from http import HTTPStatus
import pytest

pytestmark = pytest.mark.e2e

def test_generate_returns_task_id(client):
    payload = {"prompt": "A red panda", "num_inference_steps": 15, "guidance_scale": 8.0}
    r = client.post("/pictures/generate", json=payload)
    assert r.status_code == HTTPStatus.CREATED
    data = r.json()
    assert data["success"] is True
    assert isinstance(data["task_id"], str) and data["task_id"]
    assert data["status"] in ("pending", "processing", "completed", "failed")

def test_status_ok(client, monkeypatch):
    from app.pictures import dao as pictures_dao_module
    class _Stub: status = "processing"
    async def _find(*a, **k): return _Stub()
    monkeypatch.setattr(pictures_dao_module.PicturesDAO, "find_one_or_none_by_filter",
                        classmethod(lambda cls, *a, **k: _find(*a, **k)), raising=False)
    r = client.get("/pictures/status", params={"task_id": "t-1"})
    assert r.status_code == HTTPStatus.OK
    assert r.json() == "processing"

def test_status_not_found(client, monkeypatch):
    from app.pictures import dao as pictures_dao_module
    async def _find(*a, **k): return None
    monkeypatch.setattr(pictures_dao_module.PicturesDAO, "find_one_or_none_by_filter",
                        classmethod(lambda cls, *a, **k: _find(*a, **k)), raising=False)
    r = client.get("/pictures/status", params={"task_id": "missing"})
    assert r.status_code == HTTPStatus.NOT_FOUND

def test_get_picture_returns_taskinfo(client, monkeypatch):
    from app.pictures import dao as pictures_dao_module
    class _Pic:
        task_id="t-123"; user_id=1; prompt="p"; status="completed"
        filename="f.png"; s3_key="pictures/f.png"; error=None
        created_at=1761705121692; num_inference_steps=15; guidance_scale=8.0
    async def _find(*a, **k): return _Pic()
    monkeypatch.setattr(pictures_dao_module.PicturesDAO, "find_one_or_none_by_filter",
                        classmethod(lambda cls, *a, **k: _find(*a, **k)), raising=False)
    r = client.get("/pictures/t-123")
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert data["task_id"] == "t-123"
    assert data["status"] == "completed"

def test_get_pictures_list(client, monkeypatch):
    from app.pictures import dao as pictures_dao_module
    class _Pic:
        def __init__(self, i, status):
            self.task_id=f"t-{i}"; self.user_id=1; self.prompt="p"; self.status=status
            self.filename=f"f{i}.png"; self.s3_key=None; self.error=None
            self.created_at=1761705121692+i; self.num_inference_steps=15; self.guidance_scale=8.0
    async def _find_all(*a, **k): return [_Pic(1,"pending"), _Pic(2,"completed")]
    monkeypatch.setattr(pictures_dao_module.PicturesDAO, "find_all",
                        classmethod(lambda cls, *a, **k: _find_all(*a, **k)), raising=False)
    r = client.get("/pictures")
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert isinstance(data, list) and len(data) == 2
    assert {d["status"] for d in data} == {"pending","completed"}

def test_download_returns_url(client, monkeypatch):
    from app.pictures import dao as pictures_dao_module
    class _Pic: task_id="t-9"; user_id=1; s3_key="pictures/f.png"
    async def _find(*a, **k): return _Pic()
    monkeypatch.setattr(pictures_dao_module.PicturesDAO, "find_one_or_none_by_filter",
                        classmethod(lambda cls, *a, **k: _find(*a, **k)), raising=False)
    r = client.get("/pictures/download/t-9")
    assert r.status_code == HTTPStatus.OK
    assert r.json()["url"].startswith("https://")

def test_download_conflict_when_not_ready(client, monkeypatch):
    from app.pictures import dao as pictures_dao_module
    class _Pic: task_id="t-9"; user_id=1; s3_key=None
    async def _find(*a, **k): return _Pic()
    monkeypatch.setattr(pictures_dao_module.PicturesDAO, "find_one_or_none_by_filter",
                        classmethod(lambda cls, *a, **k: _find(*a, **k)), raising=False)
    r = client.get("/pictures/download/t-9")
    assert r.status_code == HTTPStatus.CONFLICT

def test_download_conflict_no_s3_key(client, monkeypatch):
    from app.pictures import dao as pictures_dao_module
    from app.pictures import s3_manager as s3_module
    class _Pic: task_id="t-9"; user_id=1; s3_key=None
    async def _find(*a, **k): return _Pic()
    called = {"count": 0}
    async def fake_url(*a, **k):
        called["count"] += 1
        return "SHOULD_NOT_BE_CALLED"

    monkeypatch.setattr(pictures_dao_module.PicturesDAO, "find_one_or_none_by_filter",
                        classmethod(lambda cls, *a, **k: _find(*a, **k)), raising=False)
    monkeypatch.setattr(s3_module.S3Manager, "get_presigned_url", fake_url, raising=False)

    r = client.get("/pictures/download/t-9")
    assert r.status_code == 409
    assert called["count"] == 0

def test_delete_picture_ok(client, monkeypatch):
    from app.pictures import dao as pictures_dao_module
    class _Pic: task_id="t-1"; user_id=1; s3_key="pictures/f.png"
    async def _find(*a, **k): return _Pic()
    async def _delete(*a, **k): return 1
    monkeypatch.setattr(pictures_dao_module.PicturesDAO, "find_one_or_none_by_filter",
                        classmethod(lambda cls, *a, **k: _find(*a, **k)), raising=False)
    monkeypatch.setattr(pictures_dao_module.PicturesDAO, "delete",
                        classmethod(lambda cls, *a, **k: _delete(*a, **k)), raising=False)
    r = client.delete("/pictures/t-1")
    assert r.status_code == HTTPStatus.NO_CONTENT

def test_request_id_header_present(client):
    r = client.get("/pictures")
    assert "X-Request-ID" in r.headers
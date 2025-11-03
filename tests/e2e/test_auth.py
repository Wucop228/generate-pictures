from http import HTTPStatus
import pytest

pytestmark = pytest.mark.e2e

def test_login_ok(client, monkeypatch):
    from app.users import dao as users_dao_module
    from app.auth import utils as auth_utils
    class _User: id=1; username="johnny"; email="john@example.com"; password="hashed"; is_admin = False
    async def _find(*a, **k): return _User()
    monkeypatch.setattr(users_dao_module.UsersDAO, "find_one_or_none",
                        classmethod(lambda cls,*a,**k:_find(*a,**k)), raising=False)
    monkeypatch.setattr(auth_utils, "verify_password", lambda p,h: True, raising=False)
    monkeypatch.setattr(auth_utils, "create_access_token", lambda uid: "token123", raising=False)

    r = client.post("/auth/login", json={"email":"john@example.com","password":"secret"})
    assert r.status_code == HTTPStatus.OK
    assert r.cookies.get("access_token") == "token123"

def test_login_wrong_password(client, monkeypatch):
    from app.users import dao as users_dao_module
    from app.auth import utils as auth_utils
    class _User: id=1; username="johnny"; email="john@example.com"; password="hashed"
    async def _find(*a, **k): return _User()
    monkeypatch.setattr(users_dao_module.UsersDAO, "find_one_or_none",
                        classmethod(lambda cls,*a,**k:_find(*a,**k)), raising=False)
    monkeypatch.setattr(auth_utils, "verify_password", lambda p,h: False, raising=False)

    r = client.post("/auth/login", json={"email":"john@example.com","password":"bad"})
    assert r.status_code == HTTPStatus.UNAUTHORIZED

def test_logout_ok(client):
    r = client.post("/auth/logout")
    assert r.status_code == HTTPStatus.OK
    assert "Успешный выход" in r.json()["message"]
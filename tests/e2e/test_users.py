from http import HTTPStatus
import pytest

pytestmark = pytest.mark.e2e

def test_register_success(client, monkeypatch):
    from app.users import dao as users_dao_module
    from app.auth import utils as auth_utils

    async def _find_one_or_none_by_filter(*a, **k): return None
    async def _add(*a, **k):
        class _User: id=10; username="johnny"; email="john@example.com"; is_admin=False
        return _User()
    monkeypatch.setattr(users_dao_module.UsersDAO, "find_one_or_none_by_filter",
                        classmethod(lambda cls,*a,**k:_find_one_or_none_by_filter(*a,**k)), raising=False)
    monkeypatch.setattr(users_dao_module.UsersDAO, "add",
                        classmethod(lambda cls,*a,**k:_add(*a,**k)), raising=False)
    monkeypatch.setattr(auth_utils, "get_password_hash", lambda p: f"hashed:{p}", raising=False)

    r = client.post("/users/register", json={
        "email":"john@example.com","password":"secret123","username":"johnny"
    })
    assert r.status_code == HTTPStatus.CREATED
    data = r.json()
    assert data["message"]

def test_register_conflict(client, monkeypatch):
    from app.users import dao as users_dao_module
    class _User: id = 1; username = "johnny"; email = "other@example.com"
    async def _find(*a, **k): return _User()
    monkeypatch.setattr(users_dao_module.UsersDAO, "find_one_or_none_by_filter",
                        classmethod(lambda cls,*a,**k:_find(*a,**k)), raising=False)
    r = client.post("/users/register", json={
        "email":"john@example.com","password":"secret123","username":"johnny"
    })
    assert r.status_code == HTTPStatus.CONFLICT

def test_change_password_ok(client, monkeypatch):
    from app.users import dao as users_dao_module
    from app.auth import utils as auth_utils
    class _User: id=1; email="john@example.com"; password="hashed:old"
    async def _find(*a, **k): return _User()
    async def _update(*a, **k): return 1
    monkeypatch.setattr(users_dao_module.UsersDAO, "find_one_or_none",
                        classmethod(lambda cls,*a,**k:_find(*a,**k)), raising=False)
    monkeypatch.setattr(users_dao_module.UsersDAO, "update",
                        classmethod(lambda cls,*a,**k:_update(*a,**k)), raising=False)
    monkeypatch.setattr(auth_utils, "verify_password", lambda p,h: p=="oldpass", raising=False)
    monkeypatch.setattr(auth_utils, "get_password_hash", lambda p: f"hashed:{p}", raising=False)

    r = client.post("/users/change-password", json={
        "email":"john@example.com","old_password":"oldpass",
        "new_password1":"newpass1","new_password2":"newpass1"
    })
    assert r.status_code == HTTPStatus.OK
    assert "Пароль" in r.json()["message"]

def test_change_password_bad_old_password(client, monkeypatch):
    from app.users import dao as users_dao_module
    from app.auth import utils as auth_utils
    class _User: id=1; email="john@example.com"; password="hashed:old"
    async def _find(*a, **k): return _User()
    monkeypatch.setattr(users_dao_module.UsersDAO, "find_one_or_none",
                        classmethod(lambda cls,*a,**k:_find(*a,**k)), raising=False)
    monkeypatch.setattr(auth_utils, "verify_password", lambda p,h: False, raising=False)

    r = client.post("/users/change-password", json={
        "email":"john@example.com","old_password":"wrong",
        "new_password1":"newpass1","new_password2":"newpass1"
    })
    assert r.status_code == HTTPStatus.UNAUTHORIZED

def test_me_ok(client, monkeypatch):
    from app.users import dao as users_dao_module
    class _User: id=1; username="johnny"; email="john@example.com"; is_admin=False
    async def _find(*a, **k): return _User()
    monkeypatch.setattr(users_dao_module.UsersDAO, "find_one_or_none",
                        classmethod(lambda cls,*a,**k:_find(*a,**k)), raising=False)
    r = client.get("/users/me")
    assert r.status_code == HTTPStatus.OK
    assert r.json()["email"] == "john@example.com"
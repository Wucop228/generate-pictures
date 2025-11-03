import uuid
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.exc import IntegrityError

pytestmark = pytest.mark.integration

@pytest.mark.asyncio
async def test_users_and_pictures_dao_sqlite(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
    Session = async_sessionmaker(engine, expire_on_commit=False)

    import app.core.database as db
    monkeypatch.setattr(db, "async_session_maker", Session, raising=True)

    async with engine.begin() as conn:
        await conn.run_sync(db.Base.metadata.create_all)

    from app.users.dao import UsersDAO
    from app.pictures.dao import PicturesDAO

    user = await UsersDAO.add(username="johnny", email="john@example.com", password="x", is_admin=False)
    assert user.id is not None

    task_id = f"t-{uuid.uuid4()}"
    pic = await PicturesDAO.add(
        user_id=user.id, task_id=task_id, prompt="p", status="pending",
        filename="f.png", s3_key=None, error=None
    )
    assert pic.id is not None

    found = await PicturesDAO.find_one_or_none(task_id=task_id)
    assert found is not None and found.user_id == user.id

    deleted = await PicturesDAO.delete(filter_by={"task_id": task_id})
    assert deleted == 1

@pytest.mark.asyncio
async def test_users_unique_email_violation(tmp_path, monkeypatch):
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core import database as db
    db_file = tmp_path / "u.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
    Session = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(db, "async_session_maker", Session, raising=True)
    async with engine.begin() as conn:
        await conn.run_sync(db.Base.metadata.create_all)

    from app.users.dao import UsersDAO

    await UsersDAO.add(username="u1", email="x@example.com", password="p", is_admin=False)
    with pytest.raises(IntegrityError):
        await UsersDAO.add(username="u2", email="x@example.com", password="p", is_admin=False)
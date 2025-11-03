from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete
from sqlalchemy.exc import SQLAlchemyError

from app.core import database as _db

class BaseDAO:
    model = None

    @classmethod
    async def find_all(cls, **filter_by):
        async with _db.async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def find_one_or_none(cls, **filter_by):
        async with _db.async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def add(cls, **values):
        async with _db.async_session_maker() as session:
            async with session.begin():
                new_instance = cls.model(**values)
                session.add(new_instance)
                try:
                    await session.commit()
                except SQLAlchemyError as e:
                    await session.rollback()
                    raise e
                return new_instance

    @classmethod
    async def update(cls, filter_by, **values):
        async with _db.async_session_maker() as session:
            async with session.begin():
                query = (
                    sqlalchemy_update(cls.model)
                    .where(*[getattr(cls.model, k) == v for k, v in filter_by.items()])
                    .values(**values)
                )
                result = await session.execute(query)
                try:
                    await session.commit()
                except SQLAlchemyError as e:
                    await session.rollback()
                    raise e
                return result.rowcount

    @classmethod
    async def find_one_or_none_by_filter(cls, *filter_conditions):
        async with _db.async_session_maker() as session:
            query = select(cls.model).filter(*filter_conditions)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def delete(cls, *, filter_by: dict) -> int:
        async with _db.async_session_maker() as session:
            try:
                result = await session.execute(
                    sqlalchemy_delete(cls.model).filter_by(**filter_by)
                )
                await session.commit()
                return getattr(result, "rowcount", 0) or 0
            except SQLAlchemyError as e:
                await session.rollback()
                raise e

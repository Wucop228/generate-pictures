from sqlalchemy import text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, int_pk

class User(Base):
    id: Mapped[int_pk]

    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str] = mapped_column(nullable=False)

    is_admin: Mapped[bool] = mapped_column(default=False, server_default=text('false'), nullable=False)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id})"
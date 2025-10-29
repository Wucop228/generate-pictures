from typing import Optional

from sqlalchemy import ForeignKey, String, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, int_pk
from app.pictures.schemas import TaskStatus
from app.users.models import User

class Picture(Base):
    id: Mapped[int_pk]

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    user: Mapped["User"] = relationship(User, lazy="joined")

    task_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus),
        index=True,
        default=TaskStatus.PENDING,
        nullable=False,
    )

    filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)

    s3_key: Mapped[Optional[str]] = mapped_column(String(1024))

    error: Mapped[Optional[str]] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, task_id={self.task_id})"
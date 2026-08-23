from datetime import datetime
from typing import Any
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2.x declarative models."""

    def __repr__(self) -> str:
        """String representation of model instances."""
        params = ", ".join(
            f"{k}={v!r}" for k, v in self.__dict__.items() if not k.startswith("_")
        )
        return f"{self.__class__.__name__}({params})"


class TimestampMixin:
    """Mixin for models requiring created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

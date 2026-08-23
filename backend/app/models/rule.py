from typing import Optional
from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, TimestampMixin


class Rule(Base, TimestampMixin):
    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rule_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    rule_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requirement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    validation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), default="HIGH", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[str] = mapped_column(String(50), default="2011", nullable=False)

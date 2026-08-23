from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.inspection import Inspection


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    barcode: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    inspections: Mapped[List["Inspection"]] = relationship(
        "Inspection", back_populates="product", cascade="all, delete-orphan"
    )

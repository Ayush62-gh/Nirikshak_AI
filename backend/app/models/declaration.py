from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.inspection import Inspection


class Declaration(Base):
    __tablename__ = "declarations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    inspection_id: Mapped[int] = mapped_column(
        ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    declaration_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    extracted_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    normalized_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    source_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bounding_box: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    inspection: Mapped["Inspection"] = relationship("Inspection", back_populates="declarations")

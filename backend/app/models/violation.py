import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.inspection import Inspection


class ViolationSeverity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class ViolationStatus(str, enum.Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class Violation(Base):
    __tablename__ = "violations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    inspection_id: Mapped[int] = mapped_column(
        ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rule_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    violation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[ViolationSeverity] = mapped_column(
        Enum(ViolationSeverity, name="violation_severity_enum", native_enum=False),
        default=ViolationSeverity.HIGH,
        nullable=False,
    )
    evidence_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    detected_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expected_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ViolationStatus] = mapped_column(
        Enum(ViolationStatus, name="violation_status_enum", native_enum=False),
        default=ViolationStatus.OPEN,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    inspection: Mapped["Inspection"] = relationship("Inspection", back_populates="violations")

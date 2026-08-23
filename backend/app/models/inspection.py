import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.product import Product
    from app.models.declaration import Declaration
    from app.models.violation import Violation
    from app.models.report import Report


class InspectionStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ComplianceResultStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    WARNING = "WARNING"


class Inspection(Base, TimestampMixin):
    __tablename__ = "inspections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    inspector_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    inspection_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    status: Mapped[InspectionStatus] = mapped_column(
        Enum(InspectionStatus, name="inspection_status_enum", native_enum=False),
        default=InspectionStatus.PENDING,
        nullable=False,
    )
    compliance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    overall_result: Mapped[ComplianceResultStatus] = mapped_column(
        Enum(ComplianceResultStatus, name="compliance_result_enum", native_enum=False),
        default=ComplianceResultStatus.PENDING,
        nullable=False,
    )

    # Relationships
    inspector: Mapped["User"] = relationship("User", back_populates="inspections")
    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="inspections")
    images: Mapped[List["InspectionImage"]] = relationship(
        "InspectionImage", back_populates="inspection", cascade="all, delete-orphan"
    )
    declarations: Mapped[List["Declaration"]] = relationship(
        "Declaration", back_populates="inspection", cascade="all, delete-orphan"
    )
    violations: Mapped[List["Violation"]] = relationship(
        "Violation", back_populates="inspection", cascade="all, delete-orphan"
    )
    report: Mapped[Optional["Report"]] = relationship(
        "Report", back_populates="inspection", uselist=False, cascade="all, delete-orphan"
    )


class InspectionImage(Base):
    __tablename__ = "inspection_images"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    inspection_id: Mapped[int] = mapped_column(
        ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    inspection: Mapped["Inspection"] = relationship("Inspection", back_populates="images")

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON
from app.db.session import Base


class Scan(Base):
    __tablename__ = "scans"

    scan_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    product_name = Column(String, nullable=True)
    manufacturer = Column(String, nullable=True)
    net_quantity = Column(String, nullable=True)
    mrp = Column(String, nullable=True)
    batch_number = Column(String, nullable=True)
    mfg_date = Column(String, nullable=True)
    consumer_care = Column(String, nullable=True)
    extracted_fields = Column(JSON, nullable=True)
    compliance_status = Column(String, nullable=False, default="PARTIAL")
    violations = Column(JSON, nullable=True)
    image_ref = Column(String, nullable=True)

    def to_dict(self) -> dict:
        return {
            "scan_id": self.scan_id,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            "product_name": self.product_name,
            "manufacturer": self.manufacturer,
            "net_quantity": self.net_quantity,
            "mrp": self.mrp,
            "batch_number": self.batch_number,
            "mfg_date": self.mfg_date,
            "consumer_care": self.consumer_care,
            "extracted_fields": self.extracted_fields,
            "compliance_status": self.compliance_status,
            "violations": self.violations,
            "image_ref": self.image_ref,
        }

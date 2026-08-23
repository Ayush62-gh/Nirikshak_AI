import os
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

Base = declarative_base()

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    if settings.DATABASE_URL.startswith("sqlite:///"):
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        db_dir = os.path.dirname(os.path.abspath(db_path))
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    from app.models.scan import Scan  # noqa: F401
    Base.metadata.create_all(bind=engine)


def save_scan(scan_data: dict) -> str:
    from app.models.scan import Scan

    db = SessionLocal()
    try:
        data = dict(scan_data)
        if not data.get("scan_id"):
            data["scan_id"] = str(uuid.uuid4())

        if "timestamp" in data and isinstance(data["timestamp"], str):
            try:
                data["timestamp"] = datetime.fromisoformat(data["timestamp"])
            except ValueError:
                data["timestamp"] = datetime.now(timezone.utc)
        elif "timestamp" not in data:
            data["timestamp"] = datetime.now(timezone.utc)

        scan_obj = Scan(**data)
        db.add(scan_obj)
        db.commit()
        db.refresh(scan_obj)
        return scan_obj.scan_id
    finally:
        db.close()


def get_scan(scan_id: str) -> dict | None:
    from app.models.scan import Scan

    db = SessionLocal()
    try:
        scan_obj = db.query(Scan).filter(Scan.scan_id == scan_id).first()
        if scan_obj:
            return scan_obj.to_dict()
        return None
    finally:
        db.close()


def list_scans(page: int = 1, limit: int = 20) -> list[dict]:
    from app.models.scan import Scan

    db = SessionLocal()
    try:
        offset = (page - 1) * limit
        scans = db.query(Scan).order_by(Scan.timestamp.desc()).offset(offset).limit(limit).all()
        return [scan.to_dict() for scan in scans]
    finally:
        db.close()

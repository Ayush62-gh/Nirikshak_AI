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


def _migrate_add_user_id_column() -> None:
    """
    Checks if 'scans' table exists and whether 'user_id' column is present.
    If missing, adds 'user_id' column and populates existing orphan records
    with an existing user ID from 'users' table to avoid data corruption or loss.
    """
    if not settings.DATABASE_URL.startswith("sqlite:///"):
        return

    import sqlite3
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    if not os.path.exists(db_path):
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scans'")
        if not cursor.fetchone():
            conn.close()
            return

        cursor.execute("PRAGMA table_info(scans)")
        columns = [col[1] for col in cursor.fetchall()]

        if "user_id" not in columns:
            cursor.execute("ALTER TABLE scans ADD COLUMN user_id VARCHAR REFERENCES users(id)")

            cursor.execute("SELECT id FROM users LIMIT 1")
            first_user = cursor.fetchone()
            if first_user:
                fallback_user_id = first_user[0]
            else:
                fallback_user_id = str(uuid.uuid4())
                cursor.execute(
                    "INSERT INTO users (id, email, full_name, hashed_password, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (fallback_user_id, "legacy_system@nirikshak.gov.in", "Legacy System User", "dummy_hash", 1, datetime.now(timezone.utc).isoformat())
                )

            cursor.execute("UPDATE scans SET user_id = ? WHERE user_id IS NULL", (fallback_user_id,))
            conn.commit()

        conn.close()
    except Exception:
        pass


def init_db() -> None:
    if settings.DATABASE_URL.startswith("sqlite:///"):
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        db_dir = os.path.dirname(os.path.abspath(db_path))
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    from app.models.scan import Scan  # noqa: F401
    from app.models.user import User  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _migrate_add_user_id_column()


def save_scan(scan_data: dict, user_id: str | None = None) -> str:
    from app.models.scan import Scan

    db = SessionLocal()
    try:
        data = dict(scan_data)
        if user_id:
            data["user_id"] = user_id
        elif not data.get("user_id"):
            raise ValueError("user_id is required to save a scan record")

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


def get_scan(scan_id: str, user_id: str | None = None) -> dict | None:
    from app.models.scan import Scan

    db = SessionLocal()
    try:
        query = db.query(Scan).filter(Scan.scan_id == scan_id)
        if user_id:
            query = query.filter(Scan.user_id == user_id)
        scan_obj = query.first()
        if scan_obj:
            return scan_obj.to_dict()
        return None
    finally:
        db.close()


def list_scans(user_id: str | None = None, page: int = 1, limit: int = 20) -> list[dict]:
    from app.models.scan import Scan

    db = SessionLocal()
    try:
        offset = (page - 1) * limit
        query = db.query(Scan)
        if user_id:
            query = query.filter(Scan.user_id == user_id)
        scans = query.order_by(Scan.timestamp.desc()).offset(offset).limit(limit).all()
        return [scan.to_dict() for scan in scans]
    finally:
        db.close()


def count_scans(user_id: str | None = None) -> int:
    from app.models.scan import Scan

    db = SessionLocal()
    try:
        query = db.query(Scan)
        if user_id:
            query = query.filter(Scan.user_id == user_id)
        return query.count()
    finally:
        db.close()


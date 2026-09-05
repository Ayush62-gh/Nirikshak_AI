import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Force test environment settings prior to module imports
TEST_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "app", "db", "test_nirikshak.db"))
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH}"

os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["USE_MOCK_OCR"] = "true"
os.environ["USE_MOCK_RULE_ENGINE"] = "true"

from app.core.config import settings
import app.db.session as db_session
from app.db.session import Base

# Point settings and sessionmaker to test database
settings.DATABASE_URL = TEST_DB_URL
settings.use_mock_ocr = True
settings.use_mock_rule_engine = True

test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
test_sessionmaker = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

db_session.engine = test_engine
db_session.SessionLocal = test_sessionmaker


@pytest.fixture(scope="session", autouse=True)
def isolate_test_database():
    """
    Session-wide fixture that creates a dedicated, isolated test database
    (test_nirikshak.db) for all pytest runs and tears it down after tests complete.
    Prevents pytest from ever modifying development nirikshak.db.
    """
    os.makedirs(os.path.dirname(TEST_DB_PATH), exist_ok=True)
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except OSError:
            pass

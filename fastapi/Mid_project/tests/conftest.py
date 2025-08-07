from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from database.models import Base
from database.session import get_db

# --- point at tests/test.db ---
TEST_DB_PATH = Path(__file__).parent / "test.db"
SQLALCHEMY_TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

# ensure stale DB is removed before tests start
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# create tables once
Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def db_session():
    # drop & recreate for strict isolation
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def client(db_session):
    # override the get_db dependency
    def override_get_db():
        return db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

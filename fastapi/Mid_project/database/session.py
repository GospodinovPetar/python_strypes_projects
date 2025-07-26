import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load environment variables from project root .env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Ensure DATABASE_URL is set
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL is not set in .env")

# Create SQLAlchemy engine and session factory
engine = create_engine(database_url, echo=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Dependency to get DB session


def get_db():
    """
    Provide a transactional scope around a series of operations.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

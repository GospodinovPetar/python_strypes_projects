import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv
from tenacity import retry, wait_fixed, stop_after_attempt

env_path = os.getenv(
    "ENV_PATH", os.path.join(os.path.dirname(__file__), "../setup/.env")
)
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in .env")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}


@retry(stop=stop_after_attempt(10), wait=wait_fixed(2))
def create_engine_with_retry():
    try:
        engine = create_engine(DATABASE_URL, connect_args=connect_args)
        with engine.connect() as connection:
            print("Database connected successfully!")
        return engine
    except OperationalError as e:
        print("Database not ready, retrying...")
        raise e


engine = create_engine_with_retry()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

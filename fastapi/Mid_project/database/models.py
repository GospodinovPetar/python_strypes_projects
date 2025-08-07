from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, String, JSON, DateTime

from database.session import engine

Base = declarative_base()

SOFIA = ZoneInfo("Europe/Sofia")


class TechNewsArticle(Base):
    __tablename__ = "technewsbg_articles"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    image_url = Column(JSON, nullable=False)
    paragraphs = Column(JSON, nullable=False)
    date = Column(String, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(SOFIA),
        server_default=text("TIMEZONE('Europe/Sofia', now())"),
        nullable=False,
    )


class WiredArticle(Base):
    __tablename__ = "wired_articles"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)

    image_url = Column(JSON, nullable=False)
    paragraphs = Column(JSON, nullable=False)
    date = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(SOFIA),
        server_default=text("TIMEZONE('Europe/Sofia', now())"),
        nullable=False,
    )


class DevNewsArticle(Base):
    __tablename__ = "devnews_articles"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    image_url = Column(JSON, nullable=False)
    paragraphs = Column(JSON, nullable=False)
    date = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(SOFIA),
        server_default=func.timezone("Europe/Sofia", func.now()),
        nullable=False,
    )


Base.metadata.create_all(bind=engine)

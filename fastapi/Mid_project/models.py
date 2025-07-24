from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import Column, Integer, String, DateTime, JSON, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

SOFIA = ZoneInfo("Europe/Sofia")


class Article(Base):
    __tablename__ = "trafficnews_articles"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True)
    title = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    date = Column(String, nullable=True)
    paragraphs = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(SOFIA),
        server_default=func.timezone("Europe/Sofia", func.now()),
        nullable=False,
    )


class NewsBgArticle(Base):
    __tablename__ = "newsbg_articles"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True)
    title = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    date = Column(String, nullable=True)
    paragraphs = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(SOFIA),
        server_default=func.timezone("Europe/Sofia", func.now()),
        nullable=False,
    )


class DevNewsArticle(Base):
    __tablename__ = "devnews_articles"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    date = Column(String, nullable=True)
    paragraphs = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(SOFIA),
        server_default=func.timezone("Europe/Sofia", func.now()),
        nullable=False,
    )

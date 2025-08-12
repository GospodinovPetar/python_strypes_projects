from __future__ import annotations
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, JSON, DateTime, UniqueConstraint, Index
from sqlalchemy.sql.functions import func

from database.session import engine

Base = declarative_base()
SOFIA = ZoneInfo("Europe/Sofia")


class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (
        UniqueConstraint("url", name="uq_articles_url"),
        # index for filtering by source
        Index("ix_articles_source", "source"),
    )

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=False)
    image_urls = Column(JSON, nullable=False, default=list)
    paragraphs = Column(JSON, nullable=False)
    date = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(SOFIA),
        server_default=func.timezone("Europe/Sofia", func.now()),
        nullable=False,
    )


Base.metadata.create_all(bind=engine)

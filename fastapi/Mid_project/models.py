from sqlalchemy import Column, String, Text, func
from sqlalchemy.dialects.postgresql.json import JSONB
from sqlalchemy.sql.sqltypes import Integer, DateTime

from db import Base


class Article(Base):
    __tablename__ = "article"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, unique=True, nullable=False, index=True)
    title = Column(Text, nullable=False)
    image_url = Column(String, nullable=True)
    date = Column(String, nullable=False)
    paragraphs = Column(JSONB, nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

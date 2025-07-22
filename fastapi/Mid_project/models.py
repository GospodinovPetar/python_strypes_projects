from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql.json import JSONB
from sqlalchemy.sql.sqltypes import Integer

from db import Base


class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    url = Column(String, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    image_url = Column(String, nullable=True)
    date = Column(String, nullable=False)
    paragraphs = Column(JSONB, nullable=False)

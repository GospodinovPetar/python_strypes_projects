from __future__ import annotations
from typing import List, Optional, Any
from pydantic import BaseModel, HttpUrl
from datetime import datetime


class ArticleBase(BaseModel):
    source: str
    url: HttpUrl
    title: str
    image_urls: List[str]
    paragraphs: List[str]
    date: Optional[str] = None
    created_at: datetime


class ArticleCreate(ArticleBase):
    pass


class ArticleOut(ArticleBase):
    id: int

    class Config:
        from_attributes = True


class ArticleInDB(ArticleOut):
    pass

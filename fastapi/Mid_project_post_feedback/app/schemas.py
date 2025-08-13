from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Any
from pydantic import BaseModel, HttpUrl
from datetime import datetime


class ArticleBase(BaseModel):
    id: int
    source: str
    url: HttpUrl
    title: str
    image_urls: List[str]
    paragraphs: List[str]
    date: Optional[str] = None
    created_at: datetime


@dataclass(frozen=True)
class ArticleData:
    source: str
    url: str
    title: str
    date: Optional[str]
    image_urls: List[str]
    paragraphs: List[str]


class ArticleCreate(ArticleBase):
    pass


class ArticleOut(ArticleBase):

    class Config:
        from_attributes = True


class ArticleInDB(ArticleOut):
    pass

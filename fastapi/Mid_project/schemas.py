from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, HttpUrl


class ArticleSchema(BaseModel):
    id: int
    url: HttpUrl
    title: str
    image_url: Optional[HttpUrl]
    date: Optional[str]
    paragraphs: List[str]
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class NewsBgArticleSchema(BaseModel):
    id: int
    url: HttpUrl
    title: str
    image_url: Optional[HttpUrl]
    date: Optional[str]
    paragraphs: List[str]
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, HttpUrl


class ArticleSchema(BaseModel):
    id: Optional[int]
    url: HttpUrl
    title: str
    date: Optional[str]
    image_url: List[str]
    paragraphs: List[str]
    created_at: Optional[datetime]

    class Config:
        orm_mode = True

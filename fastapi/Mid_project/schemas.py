from pydantic import BaseModel
from typing import List, Optional


class ArticleSchema(BaseModel):
    url: str
    title: str
    image_url: Optional[str]
    date: str
    paragraphs: List[str]

    class Config:
        orm_mode = True

from typing import List, Optional

from pydantic import BaseModel


class ArticleSchema(BaseModel):
    url: str
    title: str
    image_url: Optional[str]
    date: str
    paragraphs: List[str]

    class Config:
        orm_mode = True

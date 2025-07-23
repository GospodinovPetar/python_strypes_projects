from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from pydantic.v1 import ConfigDict
from sqlalchemy.orm import Session

from db import get_db
from models import NewsBgArticle
from schemas import ArticleSchema
from news_bg.scraper import fetch_first_recent_link, scrape_news

router = APIRouter(
    prefix="/newsbg",
    tags=["newsbg"],
)


class ScrapeRequest(BaseModel):
    url: HttpUrl

    model_config = ConfigDict(
        url_allowed_hosts={"news.bg", "www.news.bg"},
        json_schema_extra={"example": {"url": "https://news.bg/...."}},
    )


get_db_dep = Depends(get_db)


@router.get("/items", response_model=List[ArticleSchema])
def read_all_news(db: Session = get_db_dep):
    return db.query(NewsBgArticle).all()


@router.get("/items/{item_id}", response_model=ArticleSchema)
def read_item(item_id: int, db: Session = get_db_dep):
    article = db.get(NewsBgArticle, item_id)
    if not article:
        raise HTTPException(404, "Article not found")
    return article


@router.get("/latest_news_from_db/", response_model=ArticleSchema)
def latest_news_from_db(db: Session = get_db_dep):
    article = db.query(NewsBgArticle).order_by(NewsBgArticle.id.desc()).first()

    if not article:
        raise HTTPException(404, detail="Няма новини")
    return article


@router.post("/scrape/latest", response_model=ArticleSchema)
def scrape_latest(db: Session = get_db_dep):
    url = fetch_first_recent_link()
    data = scrape_news(url)
    existing = db.query(NewsBgArticle).filter_by(url=url).first()
    if existing:
        return existing
    article = NewsBgArticle(url=url, **data)
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.post("/scrape_specific", response_model=ArticleSchema)
def scrape_and_store(req: ScrapeRequest, db: Session = get_db_dep):
    url = str(req.url)
    data = scrape_news(url)
    existing = db.query(NewsBgArticle).filter_by(url=url).first()
    if existing:
        return existing
    article = NewsBgArticle(url=url, **data)
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.delete("/items/delete/{item_id}")
def delete_item(item_id: int, db: Session = get_db_dep):
    article = db.get(NewsBgArticle, item_id)
    if not article:
        raise HTTPException(404, "Article not found")
    db.delete(article)
    db.commit()
    return {"deleted_id": item_id}

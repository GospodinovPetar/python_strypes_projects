from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from pydantic.v1 import ConfigDict
from sqlalchemy.orm import Session

from db import get_db
from models import NewsBgArticle
from news_bg.scraper import fetch_first_recent_link, scrape_news
from schemas import ArticleSchema

router = APIRouter(
    prefix="/newsbg",
    tags=["newsbg"],
)


class ScrapeRequest(BaseModel):
    model_config = ConfigDict(
        url_allowed_hosts={"news.bg", "www.news.bg"},
        json_schema_extra={"example": {"url": "https://news.bg/...."}},
    )


get_db_dep = Depends(get_db)


@router.get("/items", response_model=List[ArticleSchema])
def read_all_news(db: Session = get_db_dep):
    """
    # This will give you all the traffic news in our newsbg database
    ## They will contain:
    - **id**
    - **url**
    - **title**
    - **image_url**
    - **date**
    - **paragraphs**
    - **created_at**"""
    return db.query(NewsBgArticle).all()


@router.get("/items/{item_id}", response_model=ArticleSchema)
def read_item(item_id: int, db: Session = get_db_dep):
    """
    # This will give you a newsbg article based on the id in our database
    ## It will contain:
    - **id**
    - **url**
    - **title**
    - **image_url**
    - **date**
    - **paragraphs**
    - **created_at**"""
    article = db.get(NewsBgArticle, item_id)
    if not article:
        raise HTTPException(404, "Article not found")
    return article


@router.get("/latest_news_from_db/", response_model=ArticleSchema)
def latest_news_from_db(db: Session = get_db_dep):
    """
    # This will give you the latest newsbg article in our database
    ## It will contain:
    - **id**
    - **url**
    - **title**
    - **image_url**
    - **date**
    - **paragraphs**
    - **created_at**"""

    article = db.query(NewsBgArticle).order_by(NewsBgArticle.id.desc()).first()

    if not article:
        raise HTTPException(404, detail="Няма новини")
    return article


@router.post("/scrape/latest", response_model=ArticleSchema)
def scrape_latest(db: Session = get_db_dep):
    """
    # This will give you the latest news article in news.bg
    1) We get the newest article from the website
    2) We upsert it to the database
    3) We output the article
    ## It will contain:
    - **id**
    - **url**
    - **title**
    - **image_url**
    - **date**
    - **paragraphs**
    - **created_at**
    """
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
    """
    # This will give you the info about an article you give a link to
    ## It will contain:
    - **id**
    - **url**
    - **title**
    - **image_url**
    - **date**
    - **paragraphs**
    - **created_at**
    """
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
    """
    # This will delete a specific item from the database, based on the id in our database
    """
    article = db.get(NewsBgArticle, item_id)
    if not article:
        raise HTTPException(404, "Article not found")
    db.delete(article)
    db.commit()
    return {"deleted_id": item_id}

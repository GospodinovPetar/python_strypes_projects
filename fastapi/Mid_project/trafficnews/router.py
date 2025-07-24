from typing import List

from fastapi import Depends, HTTPException, APIRouter
from pydantic import BaseModel
from pydantic.v1 import ConfigDict
from sqlalchemy.orm import Session

from db import get_db
from models import Article as ArticleModel
from schemas import ArticleSchema
from trafficnews.scraper import fetch_latest_news, scrape_trafficnews

router = APIRouter(prefix="/trafficnews", tags=["Traffic News"])
db_dependency: Session = Depends(get_db)


class ScrapeRequest(BaseModel):
    model_config = ConfigDict(
        url_allowed_hosts={"trafficnews.bg", "www.trafficnews.bg"},
        json_schema_extra={"example": {"url": "https://trafficnews.bg/...."}},
    )


@router.get(
    "/items",
    response_model=List[ArticleSchema],
    tags=["Traffic News"],
    summary="GET all the items in the database",
)
def read_all_news(db: Session = db_dependency):
    """
    # This will give you all the traffic news in our trafficnews database
    ## They will contain:
    - **id**
    - **url**
    - **title**
    - **image_url**
    - **date**
    - **paragraphs**
    - **created_at**"""
    return db.query(ArticleModel).all()


@router.get(
    "/items/{item_id}",
    response_model=ArticleSchema,
    tags=["Traffic News"],
    summary="GET a specific item",
)
def read_item(item_id: int, db: Session = db_dependency):
    """
    # This will give you a traffic news article based on the id in our database
    ## It will contain:
    - **id**
    - **url**
    - **title**
    - **image_url**
    - **date**
    - **paragraphs**
    - **created_at**"""
    return db.query(ArticleModel).get(item_id)


@router.get(
    "/latest_news_from_db/",
    response_model=ArticleSchema,
    tags=["Traffic News"],
    summary="GET the latest news from our database",
)
def latest_news_from_db(db: Session = db_dependency):
    """
    # This will give you the latest traffic news article in our database
    ## It will contain:
    - **id**
    - **url**
    - **title**
    - **image_url**
    - **date**
    - **paragraphs**
    - **created_at**"""
    article = db.query(ArticleModel).order_by(ArticleModel.id.desc()).first()

    if not article:
        raise HTTPException(404, detail="Няма новини")
    return article


@router.post(
    "/scrape/latest",
    response_model=ArticleSchema,
    tags=["Traffic News"],
    summary="POST Scrape the latest news from trafficnews",
)
def scrape_latest(db: Session = Depends(get_db)) -> ArticleModel:
    """
    # This will give you the latest news article in trafficnews
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
    news = fetch_latest_news()

    existing = db.query(ArticleModel).filter_by(url=news["url"]).first()
    if existing:
        return existing

    article = ArticleModel(**news)
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.post(
    "/scrape_specific",
    response_model=ArticleSchema,
    tags=["Traffic News"],
    summary="POST Scrape a specific article from trafficnews",
)
def scrape_and_store(req: ScrapeRequest, db: Session = db_dependency):
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
    try:
        data = scrape_trafficnews(str(req.url))
    except Exception:
        raise HTTPException(502, "Грешка при скрейпване на страницата")

    if not data["title"]:
        raise HTTPException(404, "Няма намерени данни на тази страница")

    article = db.merge(ArticleModel(url=str(req.url), **data))

    db.commit()
    return article


@router.delete(
    "/items/delete/{item_id}",
    tags=["Traffic News"],
    summary="DELETE a specific item from the database",
)
def delete_item(item_id: int, db: Session = db_dependency):
    """
    # This will deletea specific item from the database, based on the id in our database
    """
    article = db.query(ArticleModel).get(item_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    db.delete(article)
    db.commit()
    return {"Item deleted": item_id}

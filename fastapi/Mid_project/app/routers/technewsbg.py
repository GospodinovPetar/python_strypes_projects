from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from pydantic.v1 import ConfigDict
from sqlalchemy.orm import Session

from app.schemas import ArticleSchema
from app.scraper.technewsbg import fetch_latest_news, scrape_news
from database.models import TechNewsArticle
from database.session import get_db
from app.logger.logger import logger

router = APIRouter(prefix="/technewsbg", tags=["TechNewsBG"])


class ScrapeRequest(BaseModel):
    url: HttpUrl
    model_config = ConfigDict(
        url_allowed_hosts={"technews.bg", "www.technews.bg"},
        json_schema_extra={"example": {"url": "https://technews.bg/вашата-статия"}},
    )


@router.get(
    "/items", response_model=List[ArticleSchema], summary="GET all articles in DB"
)
def read_all_news(db: Session = Depends(get_db)):
    logger.info("[TECHNEWSBG] Fetching all articles from DB")
    return db.query(TechNewsArticle).all()


@router.get(
    "/items/{item_id}", response_model=ArticleSchema, summary="GET article by ID"
)
def read_item(item_id: int, db: Session = Depends(get_db)):
    article = db.get(TechNewsArticle, item_id)
    if not article:
        logger.info(f"[TECHNEWSBG] Article {item_id} not found")
        raise HTTPException(404, "Article not found")
    return article


@router.get(
    "/latest_news_from_db",
    response_model=ArticleSchema,
    summary="GET latest article from DB",
)
def latest_from_db(db: Session = Depends(get_db)):
    article = db.query(TechNewsArticle).order_by(TechNewsArticle.id.desc()).first()
    if not article:
        logger.info("[TECHNEWSBG] No articles in DB")
        raise HTTPException(404, "No articles found")
    return article


@router.post(
    "/scrape/latest",
    response_model=ArticleSchema,
    summary="Scrape and store latest news",
)
def scrape_latest(db: Session = Depends(get_db)):
    news = fetch_latest_news()
    existing = db.query(TechNewsArticle).filter_by(url=news["url"]).first()
    if existing:
        return existing
    article = TechNewsArticle(**news)
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.post(
    "/scrape_specific",
    response_model=ArticleSchema,
    summary="Scrape and store specific news",
)
def scrape_specific(req: ScrapeRequest, db: Session = Depends(get_db)):
    try:
        data = scrape_news(str(req.url))
    except Exception:
        logger.info("[TECHNEWSBG] Error scraping URL")
        raise HTTPException(502, "Error scraping the page")
    if not data.get("title"):
        raise HTTPException(404, "No data found on this page")
    data.pop("url", None)
    article = db.merge(TechNewsArticle(url=str(req.url), **data))
    db.commit()
    return article


@router.delete("/items/{item_id}", summary="Delete article by ID")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    article = db.get(TechNewsArticle, item_id)
    if not article:
        raise HTTPException(404, "Article not found")
    db.delete(article)
    db.commit()
    return {"deleted_id": item_id}

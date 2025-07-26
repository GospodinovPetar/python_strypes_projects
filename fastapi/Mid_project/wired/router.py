from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from pydantic.v1 import ConfigDict
from sqlalchemy.orm import Session

from db import get_db
from logger import logger
from models import WiredArticle
from wired.scraper import fetch_first_recent_link, scrape_news
from schemas import ArticleSchema

router = APIRouter(
    prefix="/wired",
    tags=["Wired"],
)


class ScrapeRequest(BaseModel):
    url: HttpUrl
    model_config = ConfigDict(
        url_allowed_hosts={"wired.com", "www.wired.com"},
        json_schema_extra={"example": {"url": "https://wired.com/...."}},
    )


get_db_dep = Depends(get_db)


@router.get("/items", response_model=List[ArticleSchema])
def read_all_news(db: Session = get_db_dep):
    articles = db.query(WiredArticle).all()
    if not articles:
        logger.info("[WIRED] ERROR: No articles found")
        raise HTTPException(status_code=404, detail="Няма новини")
    logger.info("[WIRED] OK: Fetching all articles from DB")
    return articles


@router.get("/items/{item_id}", response_model=ArticleSchema)
def read_item(item_id: int, db: Session = get_db_dep):
    item = db.get(WiredArticle, item_id)
    if not item:
        logger.info(f"[WIRED] ERROR: Item {item_id} not found.")
        raise HTTPException(status_code=404, detail="Item not found")
    logger.info(f"[WIRED] OK: Fetching item {item_id}")
    return item


@router.get("/latest_news_from_db/", response_model=ArticleSchema)
def latest_news_from_db(db: Session = get_db_dep):
    article = db.query(WiredArticle).order_by(WiredArticle.id.desc()).first()
    if not article:
        logger.info("[WIRED] ERROR: No articles in DB")
        raise HTTPException(status_code=404, detail="Няма новини")
    logger.info("[WIRED] OK: Fetching latest article")
    return article


@router.post("/scrape/latest", response_model=ArticleSchema)
def scrape_latest(db: Session = get_db_dep):
    url = fetch_first_recent_link()
    data = scrape_news(url)
    existing = db.query(WiredArticle).filter_by(url=url).first()
    if existing:
        logger.info("[WIRED] OK: Article exists, returning existing")
        return existing
    article = WiredArticle(url=url, **data)
    logger.info("[WIRED] OK: Scraping latest and saving to DB")
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.post("/scrape_specific", response_model=ArticleSchema)
def scrape_and_store(req: ScrapeRequest, db: Session = get_db_dep):
    url = req.url
    data = scrape_news(url)
    existing = db.query(WiredArticle).filter_by(url=str(url)).first()
    if existing:
        logger.info("[WIRED] OK: URL exists, returning existing")
        return existing
    article = WiredArticle(url=str(url), **data)
    logger.info("[WIRED] OK: Scraping specific URL and saving to DB")
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.delete("/items/delete/{item_id}")
def delete_item(item_id: int, db: Session = get_db_dep):
    article = db.get(WiredArticle, item_id)
    if not article:
        logger.info("[WIRED] ERROR: Delete; item not found.")
        raise HTTPException(status_code=404, detail="Article not found")
    db.delete(article)
    db.commit()
    logger.info(f"[WIRED] OK: Deleted item {item_id}")
    return {"Item deleted": item_id}

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from pydantic.v1 import ConfigDict
from sqlalchemy.orm import Session

from app.schemas import ArticleSchema
from app.scraper.devbgnews import fetch_first_recent_link, scrape_devnews_article
from database.models import DevNewsArticle
from database.session import get_db
from app.logger.logger import logger


router = APIRouter(
    prefix="/devnews",
    tags=["devnews"],
)

get_db_dep = Depends(get_db)


class ScrapeRequest(BaseModel):
    url: HttpUrl

    model_config = ConfigDict(
        url_allowed_hosts={"dev.bg", "www.dev.bg"},
        json_schema_extra={"example": {"url": "https://dev.bg/it-news/..."}},
    )


@router.get("/items", response_model=List[ArticleSchema])
def read_all_news(db: Session = get_db_dep):
    """
    # This will give you all the traffic news in our devbgnews database
    ## They will contain:
    - **id**
    - **url**
    - **title**
    - **image_url**
    - **date**
    - **paragraphs**
    - **created_at**"""
    article = db.query(DevNewsArticle).all()
    if not article:
        logger.info("[DEVNEWS] ERROR: A requested item was not found")
        raise HTTPException(404, detail="Няма новини")

    logger.info("[DEVNEWS] OK: Fetching latest technewsbg article from database")
    logger.debug(f"Scraped data: {article}")
    return db.query(DevNewsArticle).all()


@router.get("/items/{item_id}", response_model=ArticleSchema)
def read_item(item_id: int, db: Session = get_db_dep):
    """
    # This will give you a devbgnews article based on the id in our database
    ## It will contain:
    - **id**
    - **url**
    - **title**
    - **image_url**
    - **date**
    - **paragraphs**
    - **created_at**"""
    item = db.query(DevNewsArticle).get(item_id)

    if not item:
        logger.info(
            f"[DEVNEWS] ERROR: Fetching specific item: {item_id}, but not found."
        )
        raise HTTPException(status_code=404, detail="Item not found")
    logger.info(f"[DEVNEWS] OK: Fetching specific item: {item_id}")
    return item


@router.get("/latest_news_from_db/", response_model=ArticleSchema)
def latest_news_from_db(db: Session = get_db_dep):
    """
    # This will give you the latest devbg news article in our database
    ## It will contain:
    - **id**
    - **url**
    - **title**
    - **image_url**
    - **date**
    - **paragraphs**
    - **created_at**"""
    article = db.query(DevNewsArticle).order_by(DevNewsArticle.id.desc()).first()

    if not article:
        logger.info("[DEVNEWS] ERROR: A requested item was not found")
        raise HTTPException(404, detail="Няма новини")

    logger.info("[DEVNEWS] OK: Fetching latest technewsbg article from database")
    logger.debug(f"Scraped data: {article}")
    return article


@router.post("/scrape/latest", response_model=ArticleSchema)
def scrape_latest(db: Session = get_db_dep):
    """
    # This will give you the latest news article in dev.bg news area
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

    data = scrape_devnews_article(url)
    data.setdefault("url", url)

    existing = db.query(DevNewsArticle).filter_by(url=url).one_or_none()
    if existing:
        logger.info(
            "[DEVNEWS] OK: Requeted a scrape of an article we already have in our database, returning it, no db entries"
        )
        existing.title = data["title"]
        existing.image_url = data["image_url"]
        existing.date = data["date"]
        existing.paragraphs = data["paragraphs"]
        article = existing
    else:
        article = DevNewsArticle(**data)
        logger.info("[DEVNEWS] OK: Scraping latest news from website")
        logger.debug(f"[DEVNEWS] Scraped data: {article}")
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
    try:
        data = scrape_devnews_article(url)
    except Exception:
        logger.info(
            "[DEVNEWS] ERROR: Error scraping data from dev.bg news article",
        )
        raise HTTPException(status_code=502, detail="Error scraping the page")
    if not data.get("title"):
        logger.info(
            "[DEVNEWS] ERROR: A requested item was not found",
        )
        raise HTTPException(status_code=404, detail="No data found on this page")
    # upsert via merge
    article = db.merge(DevNewsArticle(url=url, **data))
    logger.info("[DEVNEWS] OK: Scraping latest news from url")
    logger.debug(f"[DEVNEWS] Scraped data: {article}")
    db.commit()
    db.refresh(article)
    return article


@router.delete("/items/delete/{item_id}")
def delete_item(item_id: int, db: Session = get_db_dep):
    """
    # This will delete a specific item from the database, based on the id in our database
    """
    article = db.get(DevNewsArticle, item_id)
    if not article:
        logger.info(
            "[DEVNEWS] ERROR: A delete request was opened, but no article was found."
        )
        raise HTTPException(status_code=404, detail="Article not found")
    db.delete(article)
    logger.info(
        f"[DEVNEWS] OK: Deleted a specific item from the database with id {item_id}"
    )
    db.commit()
    return {"deleted_id": item_id}

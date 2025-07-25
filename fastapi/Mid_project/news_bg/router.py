from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from pydantic.v1 import ConfigDict
from sqlalchemy.orm import Session

from db import get_db
from logger import logger
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
    article = db.query(NewsBgArticle).all()
    if not article:
        logger.info("[NEWSBG] ERROR: A requested item was not found")
        raise HTTPException(404, detail="Няма новини")

    logger.info("[NEWSBG] OK: Fetching latest trafficnews article from database")
    logger.debug(f"Scraped data: {article}")
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
    item = db.query(NewsBgArticle).get(item_id)

    if not item:
        logger.info(
            f"[NEWSBG] ERROR: Fetching specific item: {item_id}, but not found."
        )
        raise HTTPException(status_code=404, detail="Item not found")
    logger.info(f"[NEWSBG] OK: Fetching specific item: {item_id}")
    return item


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
        logger.info("[NEWSBG] ERROR: A requested item was not found")
        raise HTTPException(404, detail="Няма новини")

    logger.info("[NEWSBG] OK: Fetching latest trafficnews article from database")
    logger.debug(f"Scraped data: {article}")
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
        logger.info(
            "[NEWSBG] OK: Requeted a scrape of an article we already have in our database, returning it, no db entries"
        )
        return existing
    article = NewsBgArticle(url=url, **data)
    logger.info("[NEWSBG] OK: Scraping latest news from website")
    logger.debug(f"[NEWSBG] Scraped data: {article}")
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
        logger.info("[NEWSBG] OK: Scraping latest news from url.. Already exists in database, outputing directly from DB")
        return existing
    article = NewsBgArticle(url=url, **data)
    logger.info("[NEWSBG] OK: Scraping latest news from url")
    logger.debug(f"[NEWSBG] Scraped data: {article}")
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.delete("/items/delete/{item_id}")
def delete_item(item_id: int, db: Session = get_db_dep):
    """
    # This will delete a specific item from the database, based on the id in our database
    """
    article = db.query(NewsBgArticle).get(item_id)
    if not article:
        logger.info(
            "[NEWSBG] ERROR: A delete request was opened, but no article was found."
        )
        raise HTTPException(status_code=404, detail="Article not found")
    db.delete(article)
    logger.info(
        f"[NEWSBG] OK: Deleted a specific item from the database with id {item_id}"
    )
    db.commit()
    return {"Item deleted": item_id}

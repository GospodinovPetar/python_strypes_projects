from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, HttpUrl
from pydantic.v1 import ConfigDict
from sqlalchemy.orm import Session

from app.schemas import ArticleSchema
from app.scrapers.devbgnews import fetch_first_recent_link, scrape_devnews_article
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


@router.get("/items")
def read_all_news(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = get_db_dep,
):
    total = db.query(DevNewsArticle).count()
    articles = db.query(DevNewsArticle).offset(offset).limit(limit).all()

    if not articles:
        logger.info("[DEVNEWS] No articles found")
        return {"total": 0, "limit": limit, "offset": offset, "items": []}

    logger.info("[DEVNEWS] OK: Fetching latest devbgnews articles from database")
    logger.debug(f"Scraped data: {articles}")

    return {"total": total, "limit": limit, "offset": offset, "items": articles}


@router.get("/items/{item_id}", response_model=ArticleSchema)
def read_item(item_id: int, db: Session = get_db_dep):
    item = db.query(DevNewsArticle).filter(DevNewsArticle.id == item_id).first()

    if not item:
        logger.info(
            f"[DEVNEWS] ERROR: Fetching specific item: {item_id}, but not found."
        )
        raise HTTPException(status_code=404, detail="Item not found")
    logger.info(f"[DEVNEWS] OK: Fetching specific item: {item_id}")
    return item


@router.get("/latest_news_from_db/", response_model=ArticleSchema)
def latest_news_from_db(db: Session = get_db_dep):
    article = db.query(DevNewsArticle).order_by(DevNewsArticle.id.desc()).first()

    if not article:
        logger.info("[DEVNEWS] ERROR: A requested item was not found")
        raise HTTPException(404, detail="Няма новини")

    logger.info("[DEVNEWS] OK: Fetching latest technewsbg article from database")
    logger.debug(f"Scraped data: {article}")
    return article


@router.post("/scrape/latest", response_model=ArticleSchema)
def scrape_latest(db: Session = get_db_dep):
    url = fetch_first_recent_link()

    data = scrape_devnews_article(url)
    data.setdefault("url", url)

    existing = db.query(DevNewsArticle).filter_by(url=url).one_or_none()
    if existing:
        logger.info(
            "[DEVNEWS] OK: Requested a scrape of an article already in DB. Returning it."
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
    url = str(req.url)
    try:
        data = scrape_devnews_article(url)
    except Exception:
        logger.info("[DEVNEWS] ERROR: Error scraping data from dev.bg news article")
        raise HTTPException(status_code=502, detail="Error scraping the page")

    if not data.get("title"):
        logger.info("[DEVNEWS] ERROR: A requested item was not found")
        raise HTTPException(status_code=404, detail="No data found on this page")

    try:
        article = db.merge(DevNewsArticle(url=url, **data))
        db.commit()
        db.refresh(article)
    except Exception as e:
        db.rollback()
        logger.error(f"[DEVNEWS] ERROR: DB error during merge: {e}")
        raise HTTPException(status_code=500, detail="Database error")

    logger.info("[DEVNEWS] OK: Scraping latest news from url")
    logger.debug(f"[DEVNEWS] Scraped data: {article}")
    return article


@router.delete("/items/delete/{item_id}")
def delete_item(item_id: int, db: Session = get_db_dep):
    article = db.query(DevNewsArticle).filter(DevNewsArticle.id == item_id).first()
    if not article:
        logger.info("[DEVNEWS] ERROR: Delete request received but no article found")
        raise HTTPException(status_code=404, detail="Article not found")
    db.delete(article)
    db.commit()
    logger.info(f"[DEVNEWS] OK: Deleted article with id {item_id}")
    return {"deleted_id": item_id}

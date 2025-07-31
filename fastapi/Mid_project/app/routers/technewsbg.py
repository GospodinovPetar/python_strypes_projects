from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, HttpUrl
from pydantic.v1 import ConfigDict
from sqlalchemy.orm import Session

from app.schemas import ArticleSchema
from app.scrapers.technewsbg import fetch_latest_news, scrape_news
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


@router.get("/items", summary="GET all articles in DB")
def read_all_news(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    # This will give you paginated news in our technewsbg database
    ## Each item contains:
    - **id**
    - **url**
    - **title**
    - **image_url**
    - **date**
    - **paragraphs**
    - **created_at**

    ## Supports:
    - **limit**: Number of results per page (default=10)
    - **offset**: How many records to skip (default=0)
    """

    total = db.query(TechNewsArticle).count()
    articles = db.query(TechNewsArticle).offset(offset).limit(limit).all()

    if not articles:
        logger.info("[TECHNEWSBG] No articles found in DB")
        raise HTTPException(404, detail="Няма новини")

    logger.info(f"[TECHNEWSBG] Returning {len(articles)} articles from DB")

    return {"total": total, "limit": limit, "offset": offset, "items": articles}


@router.get(
    "/items/{item_id}",
    response_model=ArticleSchema,
    summary="GET article by ID",
)
def read_item(item_id: int, db: Session = Depends(get_db)):
    """
    # This will give you a technewsbg article based on the id in our database
    ## It will contain:
    - **id**
    - **url**
    - **title**
    - **image_url**
    - **date**
    - **paragraphs**
    - **created_at**"""
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
    """
    # This will give you the latest technewsbg news article in our database
    ## It will contain:
    - **id**
    - **url**
    - **title**
    - **image_url**
    - **date**
    - **paragraphs**
    - **created_at**"""
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
    """
    # This will give you the latest news article in technews.bg news area
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
    """
    # This will delete a specific item from the database, based on the id in our database
    """
    article = db.get(TechNewsArticle, item_id)
    if not article:
        raise HTTPException(404, "Article not found")
    db.delete(article)
    db.commit()
    return {"deleted_id": item_id}

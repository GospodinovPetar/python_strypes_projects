from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, HttpUrl
from pydantic.v1 import ConfigDict
from sqlalchemy.orm import Session

from app.schemas import ArticleSchema
from app.scrapers.wired import fetch_first_recent_link, scrape_news
from database.models import WiredArticle
from database.session import get_db
from app.logger.logger import logger

router = APIRouter(prefix="/wired", tags=["wired.com"])


class ScrapeRequest(BaseModel):
    url: HttpUrl
    model_config = ConfigDict(
        url_allowed_hosts={"wired.com", "www.wired.com"},
        json_schema_extra={"example": {"url": "https://www.wired.com/your-article"}},
    )


@router.get("/items", summary="GET all articles from DB")
def read_all_news(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    # Paginated list of all Wired articles in DB
    ## Each item includes:
    - **id**
    - **url**
    - **title**
    - **image_url**
    - **date**
    - **paragraphs**
    - **created_at**

    ## Pagination:
    - **limit**: Number of results to return (default: 10)
    - **offset**: Number of results to skip (default: 0)
    """

    total = db.query(WiredArticle).count()
    articles = db.query(WiredArticle).offset(offset).limit(limit).all()

    if not articles:
        logger.info("[WIRED] No articles found in DB")
        raise HTTPException(status_code=404, detail="No articles found")

    logger.info(
        f"[WIRED] Fetched {len(articles)} articles (offset={offset}, limit={limit})"
    )

    return {"total": total, "limit": limit, "offset": offset, "items": articles}


@router.get(
    "/items/{item_id}", response_model=ArticleSchema, summary="GET article by ID"
)
def read_item(item_id: int, db: Session = Depends(get_db)):
    """
    # This will give you a wired article based on the id in our database
    ## It will contain:
    - **id**
    - **url**
    - **title**
    - **image_url**
    - **date**
    - **paragraphs**
    - **created_at**"""
    article = db.get(WiredArticle, item_id)
    if not article:
        logger.info(f"[WIRED] Article {item_id} not found")
        raise HTTPException(status_code=404, detail="Article not found")
    logger.info(f"[WIRED] Fetching article {item_id}")
    return article


@router.get(
    "/latest_from_db",
    response_model=ArticleSchema,
    summary="GET latest article from DB",
)
def latest_from_db(db: Session = Depends(get_db)):
    """
    # This will give you the latest wired news article in our database
    ## It will contain:
    - **id**
    - **url**
    - **title**
    - **image_url**
    - **date**
    - **paragraphs**
    - **created_at**"""
    article = db.query(WiredArticle).order_by(WiredArticle.id.desc()).first()
    if not article:
        logger.info("[WIRED] No articles in DB")
        raise HTTPException(status_code=404, detail="No articles found")
    logger.info("[WIRED] Fetching latest article from DB")
    return article


@router.post(
    "/scrape/latest",
    response_model=ArticleSchema,
    summary="Scrape and save latest article",
)
def scrape_latest(db: Session = Depends(get_db)):
    """
    # This will give you the latest news article in wired.com news area
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
    try:
        url = fetch_first_recent_link()
        data = scrape_news(url)
    except Exception as e:
        logger.info(f"[WIRED] Error scraping latest: {e}")
        raise HTTPException(status_code=502, detail="Error scraping the latest article")

    existing = db.query(WiredArticle).filter_by(url=url).first()
    if existing:
        logger.info("[WIRED] Latest article exists, returning it")
        return existing

    data.pop("url", None)  # Prevent duplicate keyword arg
    article = WiredArticle(url=url, **data)

    db.add(article)
    db.commit()
    db.refresh(article)
    logger.info("[WIRED] Saved latest article to DB")
    return article


@router.post(
    "/scrape_specific",
    response_model=ArticleSchema,
    summary="Scrape and save specific article",
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
    url = str(req.url)

    existing = db.query(WiredArticle).filter_by(url=url).first()
    if existing:
        logger.info(f"[WIRED] Article already exists for URL {url}, returning from DB")
        return existing

    try:
        data = scrape_news(url)
    except Exception as e:
        logger.info(f"[WIRED] Error scraping URL {url}: {e}")
        raise HTTPException(status_code=502, detail="Error scraping the page")

    if not data.get("title"):
        logger.info(f"[WIRED] No data found at {url}")
        raise HTTPException(status_code=404, detail="No data found on this page")

    data.pop("url", None)  # Prevent duplicate keyword arg
    article = WiredArticle(url=url, **data)

    db.add(article)
    db.commit()
    db.refresh(article)
    logger.info(f"[WIRED] Saved article from {url} to DB")
    return article


@router.delete("/items/{item_id}", summary="Delete article by ID")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    """
    # This will delete a specific item from the database, based on the id in our database
    """
    article = db.get(WiredArticle, item_id)
    if not article:
        logger.info(f"[WIRED] Delete failed, article {item_id} not found")
        raise HTTPException(status_code=404, detail="Article not found")
    db.delete(article)
    db.commit()
    logger.info(f"[WIRED] Deleted article {item_id}")
    return {"deleted_id": item_id}

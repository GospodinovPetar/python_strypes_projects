from __future__ import annotations

from typing import List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from app.scrapers import scrape_site, scrape_pages, SITE_CONFIGS
from database.session import get_db
from database.models import Article


router = APIRouter(prefix="/articles", tags=["Articles"])


# -----------------------------
# Pydantic output schema
# -----------------------------
class ArticleOut(BaseModel):
    id: int
    source: str
    url: HttpUrl
    title: str
    image_urls: List[str]
    paragraphs: List[str]
    date: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2-style ORM mode


# -----------------------------
# Small helpers
# -----------------------------
def list_sites() -> List[str]:
    """Return the configured site keys from the scraper."""
    return sorted(SITE_CONFIGS.keys())


def _ensure_known_site(site: str) -> None:
    """Raise a 400 error if site key is not supported."""
    if site not in SITE_CONFIGS:
        valid = ", ".join(list_sites())
        raise HTTPException(
            status_code=400, detail=f"Unknown site '{site}'. Use one of: {valid}"
        )


def _upsert_article(db: Session, data: Any) -> Article:
    """
    Insert or update an article row based on URL.
    `data` is the scraper's ArticleData (dataclass-like with attributes).
    """
    images = getattr(data, "image_urls", None)
    if images is None:
        single = getattr(data, "image_url", None)
        images = [single] if single else []
    if not isinstance(images, list):
        images = []

    paragraphs = getattr(data, "paragraphs", None)
    if not isinstance(paragraphs, list):
        paragraphs = []

    # Prefer SQLAlchemy 2.x style get if available; fallback to query().filter().first()
    existing = db.query(Article).filter(Article.url == data.url).first()

    if existing:
        existing.title = data.title
        existing.image_urls = images
        existing.paragraphs = paragraphs
        existing.date = data.date  # Optional[str]
        existing.source = data.source
        obj = existing
    else:
        obj = Article(
            source=data.source,
            url=data.url,
            title=data.title,
            image_urls=images,
            paragraphs=paragraphs,
            date=data.date,
        )
        db.add(obj)

    db.flush()
    return obj


# -----------------------------
# Routes
# -----------------------------
@router.get("/sites", summary="List supported sites", response_model=List[str])
def get_sites() -> List[str]:
    """Show the site keys you can scrape."""
    return list_sites()


@router.post(
    "/scrape",
    summary="Scrape all articles on a chosen listing page and store them",
    response_model=List[ArticleOut],
)
def scrape_and_store(
    site: str = Query(..., description="One of /articles/sites"),
    page: int = Query(1, ge=1, description="Listing page number (1 = first page)"),
    pages: int = Query(
        1, ge=1, description="How many pages to scrape starting from 'page'"
    ),
    db: Session = Depends(get_db),
) -> List[ArticleOut]:
    """
    Scrape one or more listing pages for the selected site and upsert results
    into the `articles` table.
    """
    _ensure_known_site(site)

    # Use the scraper's API
    if pages == 1:
        items = scrape_site(site_name=site, page_number=page)
    else:
        items = scrape_pages(site_name=site, start_page=page, number_of_pages=pages)

    output: List[ArticleOut] = []
    for item in items:
        article = _upsert_article(db, item)
        output.append(ArticleOut.from_orm(article))

    db.commit()
    return output


@router.get("", summary="List stored articles", response_model=List[ArticleOut])
def list_articles(
    db: Session = Depends(get_db),
    source: Optional[str] = Query(
        None, description="Filter by source key (e.g., 'wired')"
    ),
    limit: int = Query(50, ge=1, le=200),
) -> List[ArticleOut]:
    """
    Return the most recent stored articles.
    You can filter by source and limit the number of rows.
    """
    query = db.query(Article)

    if source:
        query = query.filter(Article.source == source)

    # If your model has created_at with an index, you can order by it:
    # query = query.order_by(Article.created_at.desc())

    query = query.limit(limit)
    rows = query.all()

    results: List[ArticleOut] = []
    for row in rows:
        results.append(ArticleOut.from_orm(row))
    return results


@router.get("/{article_id}", summary="Get an article by ID", response_model=ArticleOut)
def get_article(article_id: int, db: Session = Depends(get_db)) -> ArticleOut:
    """Fetch one article by its database id."""
    article = (
        db.get(Article, article_id)
        if hasattr(db, "get")
        else db.query(Article).get(article_id)
    )
    if article is None:
        raise HTTPException(status_code=404, detail="Not found")
    return ArticleOut.from_orm(article)


@router.delete("/{article_id}", summary="Delete an article by ID")
def delete_article(article_id: int, db: Session = Depends(get_db)) -> dict:
    """Delete one article by id."""
    article = (
        db.get(Article, article_id)
        if hasattr(db, "get")
        else db.query(Article).get(article_id)
    )
    if article is None:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(article)
    db.commit()
    return {"deleted_id": article_id}

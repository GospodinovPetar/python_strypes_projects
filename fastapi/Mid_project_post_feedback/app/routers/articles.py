from __future__ import annotations

from typing import List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from app.scrapers import scrape_site, scrape_pages, SITE_CONFIGS
from database.session import get_db
from database.models import Article
from app.schemas import ArticleOut


router = APIRouter(prefix="/articles", tags=["Articles"])


def list_sites() -> List[str]:
    """
    Return the configured site keys available to the scraper.

    Returns
    -------
    List[str]
        Sorted list of site keys (e.g., ["techcrunch", "technewsbg", "wired"]).
    """
    return sorted(SITE_CONFIGS.keys())


def _ensure_known_site(site: str) -> None:
    """
    Validate that the provided site key exists in `SITE_CONFIGS`.

    Parameters
    ----------
    site : str
        Site key supplied by the client.

    Raises
    ------
    HTTPException
        400 error when the site key is not supported.
    """
    if site not in SITE_CONFIGS:
        valid = ", ".join(list_sites())
        raise HTTPException(
            status_code=400, detail=f"Unknown site '{site}'. Use one of: {valid}"
        )


def _upsert_article(db: Session, data: Any) -> Article:
    """
    Insert or update an article row based on its URL (idempotent upsert).

    Parameters
    ----------
    db : Session
        SQLAlchemy session (scoped to the request).
    data : Any
        Scraper result object (e.g., `ArticleData` dataclass) with attributes:
        - source: str
        - url: str
        - title: str
        - image_urls: list[str]
        - paragraphs: list[str]
        - date: Optional[str]

    Returns
    -------
    Article
        The persisted SQLAlchemy model instance (new or updated).
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

    existing = db.query(Article).filter(Article.url == data.url).first()

    if existing:
        existing.title = data.title
        existing.image_urls = images
        existing.paragraphs = paragraphs
        existing.date = data.date
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

    db.flush()  # ensure PK is assigned (and defaults populated if any)
    return obj


@router.get("/sites", summary="List supported sites", response_model=List[str])
def get_sites() -> List[str]:
    """
    List the site keys supported by the scraper.

    Returns
    -------
    List[str]
        Sorted array of keys you can pass to `/articles/scrape?site=...`.
    """
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
    Scrape one or more listing pages for the selected site and upsert results.

    Parameters
    ----------
    site : str
        Site key (must be present in `/articles/sites`).
    page : int
        Listing page to start from (1-based).
    pages : int
        Number of consecutive pages to scrape starting at `page`.
    db : Session
        Request-scoped SQLAlchemy session.

    Returns
    -------
    List[ArticleOut]
        Array of stored article rows (serialized).
    """
    _ensure_known_site(site)

    if pages == 1:
        items = scrape_site(site_name=site, page_number=page)
    else:
        items = scrape_pages(site_name=site, start_page=page, number_of_pages=pages)

    output: List[ArticleOut] = []
    for item in items:
        article = _upsert_article(db, item)
        # If your DB sets created_at via server default, consider db.refresh(article)
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
    Return the most recent stored articles, optionally filtered by source.

    Parameters
    ----------
    db : Session
        Request-scoped SQLAlchemy session.
    source : Optional[str]
        Site key to filter by (e.g., "wired"). If omitted, returns all sources.
    limit : int
        Maximum number of rows to return (1–200).

    Returns
    -------
    List[ArticleOut]
        The result set as API-friendly objects.
    """
    query = db.query(Article)

    if source:
        query = query.filter(Article.source == source)

    query = query.limit(limit)
    rows = query.all()

    results: List[ArticleOut] = []
    for row in rows:
        results.append(ArticleOut.from_orm(row))
    return results


@router.get("/{article_id}", summary="Get an article by ID", response_model=ArticleOut)
def get_article(article_id: int, db: Session = Depends(get_db)) -> ArticleOut:
    """
    Fetch a single article by its primary key.

    Parameters
    ----------
    article_id : int
        The article's database ID.
    db : Session
        Request-scoped SQLAlchemy session.

    Returns
    -------
    ArticleOut
        The article row serialized for API output.

    Raises
    ------
    HTTPException
        404 if the article does not exist.
    """
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
    """
    Delete a single article by its primary key.

    Parameters
    ----------
    article_id : int
        The article's database ID.
    db : Session
        Request-scoped SQLAlchemy session.

    Returns
    -------
    dict
        A confirmation payload containing the deleted ID.

    Raises
    ------
    HTTPException
        404 if the article does not exist.
    """
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

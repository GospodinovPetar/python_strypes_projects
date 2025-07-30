from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from app.main import app
from database.models import Base, DevNewsArticle
from database.session import get_db

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        return db_session
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def create_article(db_session):
    def _create(
        url: str = "https://dev.bg/test",
        title: str = "Title",
        image_url: str = "https://dev.bg/img",
        date: datetime | None = None,
        paragraphs: list[str] | None = None,
    ) -> DevNewsArticle:
        date = date or datetime.now()
        paragraphs = paragraphs or ["p1", "p2"]
        article = DevNewsArticle(
            url=url,
            title=title,
            image_url=image_url,
            date=date,
            paragraphs=paragraphs,
        )
        db_session.add(article)
        db_session.commit()
        db_session.refresh(article)
        return article

    return _create


# --- Read all news ---


def test_read_all_news_empty(client):
    resp = client.get("/devnews/items")
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_read_all_news_pagination(client, create_article):
    for i in range(5):
        create_article(url=f"https://dev.bg/a{i}")
    resp = client.get("/devnews/items?limit=2&offset=1")
    data = resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 1


# --- Read single item ---


def test_read_item_success(client, create_article):
    art = create_article()
    resp = client.get(f"/devnews/items/{art.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == art.id


def test_read_item_not_found(client):
    assert client.get("/devnews/items/9999").status_code == 404


# --- Latest news from DB ---


def test_latest_news_from_db_success(client, create_article):
    _ = create_article(url="https://dev.bg/old")
    new = create_article(url="https://dev.bg/new")
    resp = client.get("/devnews/latest_news_from_db/")
    assert resp.status_code == 200
    assert resp.json()["id"] == new.id


def test_latest_news_from_db_not_found(client):
    assert client.get("/devnews/latest_news_from_db/").status_code == 404


# --- Scrape latest ---


@patch("app.routers.devbgnews.fetch_first_recent_link")
@patch("app.routers.devbgnews.scrape_devnews_article")
def test_scrape_latest_creates_and_updates(mock_scrape, mock_link, client):
    mock_link.return_value = "https://example.com/latest"
    mock_scrape.return_value = {
        "title": "T1",
        "image_url": "https://example.com/img.jpg",
        "date": datetime.now(),
        "paragraphs": ["p"],
    }
    r1 = client.post("/devnews/scrape/latest")
    assert r1.status_code == 200
    assert r1.json()["title"] == "T1"
    mock_scrape.return_value["title"] = "T2"
    r2 = client.post("/devnews/scrape/latest")
    assert r2.status_code == 200
    assert r2.json()["title"] == "T2"


# --- Scrape specific ---


@patch("app.routers.devbgnews.scrape_devnews_article")
def test_scrape_specific_various_responses(mock_scrape, client):
    url = "https://example.com/article"
    mock_scrape.return_value = {
        "title": "Spec",
        "image_url": "https://example.com/img2.jpg",
        "date": datetime.now(),
        "paragraphs": ["x"],
    }
    assert client.post("/devnews/scrape_specific", json={"url": url}).status_code == 200
    mock_scrape.side_effect = Exception()
    assert client.post("/devnews/scrape_specific", json={"url": url}).status_code == 502
    mock_scrape.side_effect = None
    mock_scrape.return_value = {}
    assert client.post("/devnews/scrape_specific", json={"url": url}).status_code == 404


# --- Delete item ---


def test_delete_item_success(client, create_article):
    art = create_article()
    resp = client.delete(f"/devnews/items/delete/{art.id}")
    assert resp.status_code == 200
    assert resp.json()["deleted_id"] == art.id


def test_delete_item_not_found(client):
    assert client.delete("/devnews/items/delete/9999").status_code == 404

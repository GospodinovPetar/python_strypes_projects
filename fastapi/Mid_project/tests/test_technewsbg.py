from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from database.models import TechNewsArticle


@pytest.fixture
def create_tech_article(db_session):
    def create_new_tech_article(
        url: str = "https://technews.bg/test-article",
        title: str = "Sample Title",
        images: list[str] | None = None,
        published_date: datetime | None = None,
        paragraphs: list[str] | None = None,
    ) -> TechNewsArticle:
        published_date = published_date or datetime.now()
        images = images or ["https://technews.bg/default-image.jpg"]
        paragraphs = paragraphs or ["First paragraph.", "Second paragraph."]
        # Create and save the article
        article = TechNewsArticle(
            url=url,
            title=title,
            image_url=images,
            date=published_date,
            paragraphs=paragraphs,
        )
        db_session.add(article)
        db_session.commit()
        db_session.refresh(article)
        return article

    return create_new_tech_article


def test_get_all_articles_empty(client: TestClient):
    response = client.get("/technewsbg/items")
    assert response.status_code == 404
    assert response.json()["detail"] == "Няма новини"


def test_get_articles_with_pagination(client: TestClient, create_tech_article):
    for i in range(5):
        create_tech_article(url=f"https://technews.bg/article{i}")
    response = client.get("/technewsbg/items?limit=2&offset=1")
    data = response.json()
    assert response.status_code == 200
    assert data["total"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 1
    assert len(data["items"]) == 2


def test_get_article_by_id_success(client: TestClient, create_tech_article):
    saved = create_tech_article()
    response = client.get(f"/technewsbg/items/{saved.id}")
    data = response.json()
    assert response.status_code == 200
    assert data["id"] == saved.id


def test_get_article_by_id_not_found(client: TestClient):
    response = client.get("/technewsbg/items/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Article not found"


def test_get_latest_article_success(client: TestClient, create_tech_article):
    create_tech_article(url="https://technews.bg/old")
    latest = create_tech_article(url="https://technews.bg/newest")
    response = client.get("/technewsbg/latest_news_from_db")
    data = response.json()
    assert response.status_code == 200
    assert data["id"] == latest.id


def test_get_latest_article_not_found(client: TestClient):
    response = client.get("/technewsbg/latest_news_from_db")
    assert response.status_code == 404
    assert response.json()["detail"] == "No articles found"


@patch("app.routers.technewsbg.fetch_latest_news")
def test_scrape_latest_article_returns_existing(mock_fetch, client: TestClient):
    mock_fetch.return_value = {
        "url": "https://example.com/latest",
        "title": "Tech Title",
        "image_url": ["https://example.com/img.jpg"],
        "date": datetime.now(),
        "paragraphs": ["Hello world!"],
    }
    # First POST creates the article
    first = client.post("/technewsbg/scrape/latest")
    assert first.status_code == 200
    assert first.json()["title"] == "Tech Title"
    # цхекинг фор упдайтед дата
    mock_fetch.return_value["title"] = "New Title"
    second = client.post("/technewsbg/scrape/latest")
    assert second.status_code == 200
    assert second.json()["title"] == "Tech Title"


@patch("app.routers.technewsbg.scrape_news")
def test_scrape_specific_article(mock_scrape, client: TestClient):
    test_url = "https://technews.bg/some-article"
    mock_scrape.return_value = {
        "title": "Specific Tech",
        "image_url": ["https://example.com/tech.jpg"],
        "date": datetime.now(),
        "paragraphs": ["Tech paragraph."],
    }
    ok = client.post("/technewsbg/scrape_specific", json={"url": test_url})
    assert ok.status_code == 200
    assert ok.json()["title"] == "Specific Tech"
    mock_scrape.side_effect = Exception("fail")
    bad = client.post("/technewsbg/scrape_specific", json={"url": test_url})
    assert bad.status_code == 502
    assert bad.json()["detail"] == "Error scraping the page"
    mock_scrape.side_effect = None
    mock_scrape.return_value = {}
    missing = client.post("/technewsbg/scrape_specific", json={"url": test_url})
    assert missing.status_code == 404
    assert missing.json()["detail"] == "No data found on this page"


def test_delete_article(client: TestClient, create_tech_article):
    art = create_tech_article()
    deleted = client.delete(f"/technewsbg/items/{art.id}")
    data = deleted.json()
    assert deleted.status_code == 200
    assert data["deleted_id"] == art.id


def test_delete_article_not_found(client: TestClient):
    resp = client.delete("/technewsbg/items/9999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Article not found"

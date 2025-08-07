from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from database.models import TechNewsArticle


# Fixtures


@pytest.fixture
def create_tech_article(db_session):
    """
    Fixture that creates and saves a TechNewsArticle in the test database.
    """

    def create(
        url: str = "https://technews.bg/test-article",
        title: str = "Sample Title",
        images: list[str] | None = None,
        published_date: datetime | None = None,
        paragraphs: list[str] | None = None,
    ) -> TechNewsArticle:
        article = TechNewsArticle(
            url=url,
            title=title,
            image_url=images or ["https://technews.bg/default-image.jpg"],
            date=published_date or datetime.now(),
            paragraphs=paragraphs or ["First paragraph.", "Second paragraph."],
        )
        db_session.add(article)
        db_session.commit()
        db_session.refresh(article)
        return article

    return create


# Read Tests


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
    article = create_tech_article()
    response = client.get(f"/technewsbg/items/{article.id}")
    data = response.json()

    assert response.status_code == 200
    assert data["id"] == article.id


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


# Scraping Tests


@patch("app.routers.technewsbg.fetch_latest_news")
def test_scrape_latest_article_returns_existing(mock_fetch, client: TestClient):
    """
    Tests that an already scraped article is not duplicated.
    """
    mock_fetch.return_value = {
        "url": "https://example.com/latest",
        "title": "Tech Title",
        "image_url": ["https://example.com/img.jpg"],
        "date": datetime.now(),
        "paragraphs": ["Hello world!"],
    }

    # First scrape (saves the article)
    first = client.post("/technewsbg/scrape/latest")
    assert first.status_code == 200
    assert first.json()["title"] == "Tech Title"

    # Change title in mock, but second call should return the original
    mock_fetch.return_value["title"] = "New Title"
    second = client.post("/technewsbg/scrape/latest")
    assert second.status_code == 200
    assert second.json()["title"] == "Tech Title"


@patch("app.routers.technewsbg.scrape_news")
def test_scrape_specific_article(mock_scrape, client: TestClient):
    """
    Tests three scraping outcomes: success, error, and no data.
    """
    url_success = "https://technews.bg/article-success"
    mock_scrape.return_value = {
        "title": "Specific Tech",
        "image_url": ["https://example.com/tech.jpg"],
        "date": datetime.now(),
        "paragraphs": ["Tech paragraph."],
    }

    ok = client.post("/technewsbg/scrape_specific", json={"url": url_success})
    assert ok.status_code == 200
    assert ok.json()["title"] == "Specific Tech"

    url_error = "https://technews.bg/article-error"
    mock_scrape.side_effect = Exception("fail")

    error = client.post("/technewsbg/scrape_specific", json={"url": url_error})
    assert error.status_code == 502
    assert error.json()["detail"] == "Error scraping the page"

    url_empty = "https://technews.bg/article-empty"
    mock_scrape.side_effect = None
    mock_scrape.return_value = {}

    missing = client.post("/technewsbg/scrape_specific", json={"url": url_empty})
    assert missing.status_code == 404
    assert missing.json()["detail"] == "No data found on this page"


# Delete Tests


def test_delete_article(client: TestClient, create_tech_article):
    article = create_tech_article()
    response = client.delete(f"/technewsbg/items/{article.id}")
    data = response.json()

    assert response.status_code == 200
    assert data["deleted_id"] == article.id


def test_delete_article_not_found(client: TestClient):
    response = client.delete("/technewsbg/items/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Article not found"

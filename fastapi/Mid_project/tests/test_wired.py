from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from database.models import WiredArticle


# Fixtures


@pytest.fixture
def create_wired_article(db_session):
    """
    Fixture to create and save a WiredArticle in the test database.
    """

    def create(
        article_url: str = "https://wired.com/test",
        article_title: str = "Sample Title",
        article_image_urls: list[str] | None = None,
        article_date: datetime | None = None,
        article_paragraphs: list[str] | None = None,
    ) -> WiredArticle:
        article = WiredArticle(
            url=article_url,
            title=article_title,
            image_url=article_image_urls or ["https://wired.com/img"],
            date=article_date or datetime.now(),
            paragraphs=article_paragraphs or ["Paragraph A", "Paragraph B"],
        )
        db_session.add(article)
        db_session.commit()
        db_session.refresh(article)
        return article

    return create


# Read Tests


def test_read_all_wired_articles_empty(client: TestClient):
    response = client.get("/wired/items")

    assert response.status_code == 404
    assert response.json()["detail"] == "No articles found"


def test_read_all_wired_articles_with_pagination(
    client: TestClient, create_wired_article
):
    for i in range(5):
        create_wired_article(article_url=f"https://wired.com/article{i}")

    response = client.get("/wired/items?limit=2&offset=1")
    data = response.json()

    assert response.status_code == 200
    assert data["total"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 1
    assert len(data["items"]) == 2


def test_read_wired_article_by_id_success(client: TestClient, create_wired_article):
    article = create_wired_article()
    response = client.get(f"/wired/items/{article.id}")
    data = response.json()

    assert response.status_code == 200
    assert data["id"] == article.id


def test_read_wired_article_by_id_not_found(client: TestClient):
    response = client.get("/wired/items/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Article not found"


def test_latest_wired_article_from_db_success(client: TestClient, create_wired_article):
    create_wired_article(article_url="https://wired.com/old")
    latest = create_wired_article(article_url="https://wired.com/new")

    response = client.get("/wired/latest_from_db")
    data = response.json()

    assert response.status_code == 200
    assert data["id"] == latest.id


def test_latest_wired_article_from_db_not_found(client: TestClient):
    response = client.get("/wired/latest_from_db")

    assert response.status_code == 404
    assert response.json()["detail"] == "No articles found"


# Scraping Tests


@patch("app.routers.wired.scrape_news")
@patch("app.routers.wired.fetch_first_recent_link")
def test_scrape_latest_wired_article_creates_or_returns_existing(
    mock_fetch_recent_link, mock_scrape_news, client: TestClient
):
    mock_fetch_recent_link.return_value = "https://example.com/latest-wired"
    mock_scrape_news.return_value = {
        "title": "Wired Title",
        "image_url": ["https://example.com/wired.jpg"],
        "date": datetime.now(),
        "paragraphs": ["First line"],
    }

    first = client.post("/wired/scrape/latest")
    assert first.status_code == 200
    assert first.json()["title"] == "Wired Title"

    mock_scrape_news.return_value = {
        "title": "Updated Wired",
        "image_url": ["https://example.com/wired.jpg"],
        "date": datetime.now(),
        "paragraphs": ["Second line"],
    }

    second = client.post("/wired/scrape/latest")
    assert second.status_code == 200
    assert second.json()["paragraphs"] == ["First line"]


@patch("app.routers.wired.scrape_news")
def test_scrape_specific_wired_article_success(
    mock_scrape_function, client: TestClient
):
    test_url = "https://wired.com/specific"
    mock_scrape_function.return_value = {
        "title": "Specific Wired Title",
        "image_url": ["https://example.com/specific.jpg"],
        "date": datetime.now(),
        "paragraphs": ["Detail line"],
    }

    response = client.post("/wired/scrape_specific", json={"url": test_url})

    assert response.status_code == 200
    assert response.json()["title"] == "Specific Wired Title"


@patch("app.routers.wired.scrape_news")
def test_scrape_specific_wired_article_error(mock_scrape_function, client: TestClient):
    test_url = "https://wired.com/error"
    mock_scrape_function.side_effect = Exception("scrape failed")

    response = client.post("/wired/scrape_specific", json={"url": test_url})

    assert response.status_code == 502
    assert response.json()["detail"] == "Error scraping the page"


@patch("app.routers.wired.scrape_news")
def test_scrape_specific_wired_article_not_found(
    mock_scrape_function, client: TestClient
):
    test_url = "https://wired.com/notfound"
    mock_scrape_function.return_value = {}

    response = client.post("/wired/scrape_specific", json={"url": test_url})

    assert response.status_code == 404
    assert response.json()["detail"] == "No data found on this page"


# Delete Tests


def test_delete_wired_article_success(client: TestClient, create_wired_article):
    article = create_wired_article()
    response = client.delete(f"/wired/items/{article.id}")
    data = response.json()

    assert response.status_code == 200
    assert data["deleted_id"] == article.id


def test_delete_wired_article_not_found(client: TestClient):
    response = client.delete("/wired/items/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Article not found"

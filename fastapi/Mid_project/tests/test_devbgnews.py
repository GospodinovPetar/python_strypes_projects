from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from database.models import DevNewsArticle


# Fixtures


@pytest.fixture
def create_dev_article(db_session):
    """
    Fixture that creates and saves a DevNewsArticle in the test database.
    """

    def create(
        article_url: str = "https://dev.bg/test",
        article_title: str = "Sample Title",
        article_image_urls: list[str] | None = None,
        article_date: datetime | None = None,
        article_paragraphs: list[str] | None = None,
    ) -> DevNewsArticle:
        article = DevNewsArticle(
            url=article_url,
            title=article_title,
            image_url=article_image_urls or ["https://dev.bg/img"],
            date=article_date or datetime.now(),
            paragraphs=article_paragraphs or ["Paragraph 1", "Paragraph 2"],
        )
        db_session.add(article)
        db_session.commit()
        db_session.refresh(article)
        return article

    return create


# Read Tests


def test_read_all_news_empty(client: TestClient):
    response = client.get("/devnews/items")
    data = response.json()

    assert response.status_code == 404


def test_read_all_news_with_pagination(client: TestClient, create_dev_article):
    for i in range(5):
        create_dev_article(article_url=f"https://dev.bg/article{i}")

    response = client.get("/devnews/items?limit=2&offset=1")
    data = response.json()

    assert response.status_code == 200
    assert data["total"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 1
    assert len(data["items"]) == 2


def test_read_single_article_success(client: TestClient, create_dev_article):
    article = create_dev_article()
    response = client.get(f"/devnews/items/{article.id}")
    data = response.json()

    assert response.status_code == 200
    assert data["id"] == article.id


def test_read_single_article_not_found(client: TestClient):
    response = client.get("/devnews/items/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Article not found"


def test_latest_news_from_db_success(client: TestClient, create_dev_article):
    create_dev_article(article_url="https://dev.bg/old")
    latest_article = create_dev_article(article_url="https://dev.bg/new")

    response = client.get("/devnews/latest_news_from_db/")
    data = response.json()

    assert response.status_code == 200
    assert data["id"] == latest_article.id


def test_latest_news_from_db_not_found(client: TestClient):
    response = client.get("/devnews/latest_news_from_db/")

    assert response.status_code == 404
    assert response.json()["detail"] == "No articles found"


# Scraping Tests


@patch("app.routers.devbgnews.fetch_first_recent_link")
@patch("app.routers.devbgnews.scrape_devnews_article")
def test_scrape_latest_article_updates_or_creates(
    mock_scrape_function, mock_fetch_link, client: TestClient
):
    mock_fetch_link.return_value = "https://example.com/latest-article"

    mock_scrape_function.return_value = {
        "title": "Initial Title",
        "image_url": ["https://example.com/image.jpg"],
        "date": datetime.now(),
        "paragraphs": ["First paragraph"],
    }

    first_response = client.post("/devnews/scrape/latest")
    first_data = first_response.json()

    assert first_response.status_code == 200
    assert first_data["title"] == "Initial Title"

    mock_scrape_function.return_value["title"] = "Updated Title"

    second_response = client.post("/devnews/scrape/latest")
    second_data = second_response.json()

    assert second_response.status_code == 200
    assert second_data["title"] == "Updated Title"


@patch("app.routers.devbgnews.scrape_devnews_article")
def test_scrape_specific_article_various_outcomes(
    mock_scrape_function, client: TestClient
):
    url_success = "https://example.com/article-success"
    mock_scrape_function.return_value = {
        "title": "Specific Title",
        "image_url": ["https://example.com/image2.jpg"],
        "date": datetime.now(),
        "paragraphs": ["Content paragraph"],
    }

    response_success = client.post(
        "/devnews/scrape_specific", json={"url": url_success}
    )
    assert response_success.status_code == 200

    url_error = "https://example.com/article-error"
    mock_scrape_function.side_effect = Exception("network error")

    response_error = client.post("/devnews/scrape_specific", json={"url": url_error})
    assert response_error.status_code == 502
    assert response_error.json()["detail"] == "Error scraping the page"

    url_empty = "https://example.com/article-empty"
    mock_scrape_function.side_effect = None
    mock_scrape_function.return_value = {}

    response_missing = client.post("/devnews/scrape_specific", json={"url": url_empty})
    assert response_missing.status_code == 404
    assert response_missing.json()["detail"] == "No data found on this page"


# Delete Tests


def test_delete_article_success(client: TestClient, create_dev_article):
    article = create_dev_article()
    response = client.delete(f"/devnews/items/delete/{article.id}")
    data = response.json()

    assert response.status_code == 200
    assert data["deleted_id"] == article.id


def test_delete_article_not_found(client: TestClient):
    response = client.delete("/devnews/items/delete/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Article not found"

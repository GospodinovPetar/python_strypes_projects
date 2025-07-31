from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from database.models import WiredArticle


@pytest.fixture
def create_wired_article(db_session):
    def create_new_wired_article(
        article_url: str = "https://wired.com/test",
        article_title: str = "Sample Title",
        article_image_urls: list[str] = None,
        article_date: datetime = None,
        article_paragraphs: list[str] = None,
    ) -> WiredArticle:
        article_date = article_date or datetime.now()
        article_image_urls = article_image_urls or ["https://wired.com/img"]
        article_paragraphs = article_paragraphs or ["Paragraph A", "Paragraph B"]
        # Saving the WiredArticle
        new_article = WiredArticle(
            url=article_url,
            title=article_title,
            image_url=article_image_urls,
            date=article_date,
            paragraphs=article_paragraphs,
        )
        db_session.add(new_article)
        db_session.commit()
        db_session.refresh(new_article)
        return new_article

    return create_new_wired_article


def test_read_all_wired_articles_empty(client: TestClient):
    response = client.get("/wired/items")
    assert response.status_code == 404
    assert response.json()["detail"] == "No articles available"


def test_read_all_wired_articles_with_pagination(
    client: TestClient, create_wired_article
):
    for index in range(5):
        create_wired_article(article_url=f"https://wired.com/article{index}")

    response = client.get("/wired/items?limit=2&offset=1")
    response_data = response.json()
    assert response.status_code == 200
    assert response_data["total"] == 5
    assert response_data["limit"] == 2
    assert response_data["offset"] == 1
    assert len(response_data["items"]) == 2


def test_read_wired_article_by_id_success(client: TestClient, create_wired_article):
    created_article = create_wired_article()
    response = client.get(f"/wired/items/{created_article.id}")
    response_data = response.json()
    assert response.status_code == 200
    assert response_data["id"] == created_article.id


def test_read_wired_article_by_id_not_found(client: TestClient):
    response = client.get("/wired/items/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Article not found"


def test_latest_wired_article_from_db_success(client: TestClient, create_wired_article):
    _ = create_wired_article(article_url="https://wired.com/old")
    most_recent = create_wired_article(article_url="https://wired.com/new")
    response = client.get("/wired/latest_from_db")
    response_data = response.json()
    assert response.status_code == 200
    assert response_data["id"] == most_recent.id


def test_latest_wired_article_from_db_not_found(client: TestClient):
    response = client.get("/wired/latest_from_db")
    assert response.status_code == 404
    assert response.json()["detail"] == "No articles available"


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
    first_response = client.post("/wired/scrape/latest")
    first_data = first_response.json()
    assert first_response.status_code == 200
    assert first_data["title"] == "Wired Title"

    mock_scrape_news.return_value = {
        "title": "Updated Wired",
        "image_url": ["https://example.com/wired.jpg"],
        "date": datetime.now(),
        "paragraphs": ["Second line"],
    }
    second_response = client.post("/wired/scrape/latest")
    second_data = second_response.json()
    assert second_response.status_code == 200
    assert second_data["paragraphs"] == ["First line"]


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


def test_delete_wired_article_success(client: TestClient, create_wired_article):
    article_to_delete = create_wired_article()
    response = client.delete(f"/wired/items/{article_to_delete.id}")
    data = response.json()
    assert response.status_code == 200
    assert data["deleted_id"] == article_to_delete.id


def test_delete_wired_article_not_found(client: TestClient):
    response = client.delete("/wired/items/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Article not found"

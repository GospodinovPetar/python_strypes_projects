from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from database.models import DevNewsArticle


@pytest.fixture
def create_dev_article(db_session):
    def create_new_dev_article(
        article_url: str = "https://dev.bg/test",
        article_title: str = "Sample Title",
        article_image_urls: list[str] | None = None,
        article_date: datetime | None = None,
        article_paragraphs: list[str] | None = None,
    ) -> DevNewsArticle:
        # Provide defaults if None
        article_date = article_date or datetime.now()
        article_image_urls = article_image_urls or ["https://dev.bg/img"]
        article_paragraphs = article_paragraphs or ["Paragraph 1", "Paragraph 2"]
        new_article = DevNewsArticle(
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

    return create_new_dev_article


def test_read_all_news_empty(client: TestClient):
    # When no articles exist, calling the endpoint should return total=0 and an empty list
    response = client.get("/devnews/items")
    response_data = response.json()
    assert response_data["total"] == 0
    assert response_data["items"] == []


def test_read_all_news_with_pagination(client: TestClient, create_dev_article):
    # Creating 5 mock articles
    for index in range(5):
        create_dev_article(article_url=f"https://dev.bg/article{index}")

    response = client.get("/devnews/items?limit=2&offset=1")
    response_data = response.json()
    assert response_data["total"] == 5
    assert response_data["limit"] == 2
    assert response_data["offset"] == 1
    assert len(response_data["items"]) == 2


def test_read_single_article_success(client: TestClient, create_dev_article):
    created_article = create_dev_article()
    response = client.get(f"/devnews/items/{created_article.id}")
    response_data = response.json()
    assert response.status_code == 200
    assert response_data["id"] == created_article.id


def test_read_single_article_not_found(client: TestClient):
    response = client.get("/devnews/items/9999")
    assert response.status_code == 404


def test_latest_news_from_db_success(client: TestClient, create_dev_article):
    _old_article = create_dev_article(article_url="https://dev.bg/old")
    newest_article = create_dev_article(article_url="https://dev.bg/new")
    response = client.get("/devnews/latest_news_from_db/")
    response_data = response.json()
    assert response.status_code == 200
    assert response_data["id"] == newest_article.id


def test_latest_news_from_db_not_found(client: TestClient):
    # No articles in DB should yield a 404
    response = client.get("/devnews/latest_news_from_db/")
    assert response.status_code == 404


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
    test_url = "https://example.com/specific-article"

    mock_scrape_function.return_value = {
        "title": "Specific Title",
        "image_url": ["https://example.com/image2.jpg"],
        "date": datetime.now(),
        "paragraphs": ["Content paragraph"],
    }
    success_response = client.post("/devnews/scrape_specific", json={"url": test_url})
    assert success_response.status_code == 200

    mock_scrape_function.side_effect = Exception("network error")
    error_response = client.post("/devnews/scrape_specific", json={"url": test_url})
    assert error_response.status_code == 502

    mock_scrape_function.side_effect = None
    mock_scrape_function.return_value = {}
    not_found_response = client.post("/devnews/scrape_specific", json={"url": test_url})
    assert not_found_response.status_code == 404


def test_delete_article_success(client: TestClient, create_dev_article):
    article_to_delete = create_dev_article()
    delete_response = client.delete(f"/devnews/items/delete/{article_to_delete.id}")
    delete_data = delete_response.json()

    assert delete_response.status_code == 200
    assert delete_data["deleted_id"] == article_to_delete.id


def test_delete_article_not_found(client: TestClient):
    delete_response = client.delete("/devnews/items/delete/9999")
    assert delete_response.status_code == 404
    assert delete_response.json()["detail"] == "Article not found"

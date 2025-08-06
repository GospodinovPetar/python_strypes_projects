from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

TECHNEWS_BASE_URL = "https://technews.bg"
TECHNEWS_HEADERS = {"User-Agent": "TechNewsScraper"}


def _get_page_html(url: str, headers: dict) -> str:
    """Fetches the page HTML using the given headers."""
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text


def get_page_html(url: str) -> str:
    """Fetches HTML from TechNews.bg."""
    return _get_page_html(url, TECHNEWS_HEADERS)


def fetch_latest_news() -> dict:
    html = get_page_html(TECHNEWS_BASE_URL)
    soup = BeautifulSoup(html, "html.parser")

    link = soup.select_one("article.hentry a[href]")
    if not link:
        raise RuntimeError(
            "Could not find the latest article link on TechNews.bg homepage"
        )

    href = link["href"]
    article_url = href if href.startswith("http") else urljoin(TECHNEWS_BASE_URL, href)

    return scrape_news(article_url)


def scrape_news(url: str) -> dict:
    html = get_page_html(url)
    soup = BeautifulSoup(html, "html.parser")

    # Title
    title_tag = soup.select_one("h1.entry-title")
    title = title_tag.get_text(strip=True) if title_tag else None

    # Publish date
    time_tag = soup.select_one("time.entry-date.published")
    if time_tag and time_tag.has_attr("datetime"):
        date = time_tag["datetime"]
    elif time_tag:
        date = time_tag.get_text(strip=True)
    else:
        date = None

    # Images
    image_url = []
    body = soup.select_one("div.entry-content") or soup.select_one("article")
    if body:
        for img in body.find_all("img"):
            src = img.get("data-src") or img.get("src")
            if src and not src.startswith("data:"):
                full_src = src if src.startswith("http") else urljoin(url, src)
                image_url.append(full_src)

    # Paragraphs
    paragraphs = []
    if body:
        paragraphs = [
            p.get_text(strip=True) for p in body.find_all("p") if p.get_text(strip=True)
        ]

    return {
        "url": url,
        "title": title,
        "date": date,
        "image_url": image_url,
        "paragraphs": paragraphs,
    }

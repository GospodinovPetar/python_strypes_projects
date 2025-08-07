from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.wired.com"
HEADERS = {"User-Agent": "NewsScraper"}


def _get_page_html(url: str, headers: dict) -> str:
    """Fetches the page HTML using the given headers."""
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text


def get_page_html(source: str) -> str:
    """Fetches Wired page HTML."""
    return _get_page_html(source, HEADERS)


def fetch_first_recent_link() -> str:
    html = get_page_html(BASE_URL)
    soup = BeautifulSoup(html, "html.parser")
    link = soup.select_one('a[href*="/story/"]')
    if not link:
        raise RuntimeError("Could not find any article links on the homepage.")
    return urljoin(BASE_URL, link["href"])


def scrape_news(source: str) -> dict:
    html = get_page_html(source)
    soup = BeautifulSoup(html, "html.parser")

    # Title
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else None

    # Date
    time_tag = soup.find("time")
    date = None
    if time_tag:
        date = time_tag.get("datetime") or time_tag.get_text(strip=True)

    # Images
    image_url = []
    body = soup.find("div", itemprop="articleBody") or soup.find("article")
    if body:
        image_url = [img["src"] for img in body.find_all("img", src=True)]

    # Paragraphs
    paragraphs = []
    if body:
        paragraphs = [
            p.get_text(strip=True) for p in body.find_all("p") if p.get_text(strip=True)
        ]

    return {
        "url": source,
        "title": title,
        "date": date,
        "image_url": image_url,
        "paragraphs": paragraphs,
    }

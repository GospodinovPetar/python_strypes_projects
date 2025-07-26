from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# --- Configuration ---
BASE_URL = "https://technews.bg"
HEADERS = {"User-Agent": "TechNewsScraper"}


def get_page_html(url: str) -> str:
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.text


def fetch_latest_news() -> dict:
    html = get_page_html(BASE_URL)
    soup = BeautifulSoup(html, "html.parser")

    link = soup.select_one("article.hentry a[href]")
    if not link:
        raise RuntimeError(
            "Could not find the latest article link on TechNews.bg homepage"
        )

    href = link["href"]
    article_url = href if href.startswith("http") else urljoin(BASE_URL, href)

    return scrape_news(article_url)


def scrape_news(url: str) -> dict:
    html = get_page_html(url)
    soup = BeautifulSoup(html, "html.parser")

    # Title
    title = soup.select_one("h1.entry-title")
    title = title.get_text(strip=True) if title else None

    # Publish date
    time = soup.select_one("time.entry-date.published")
    if time and time.has_attr("datetime"):
        date = time["datetime"]
    elif time:
        date = time.get_text(strip=True)
    else:
        date = None

    # Article body
    body = soup.select_one("div.entry-content") or soup.select_one("article")

    # Images
    images = []
    if body:
        for img in body.find_all("img"):
            src = img.get("data-src") or img.get("src")
            if src and not src.startswith("data:"):
                full_src = src if src.startswith("http") else urljoin(url, src)
                images.append(full_src)

    # Paragraphs: all non-empty p text
    paragraphs = []
    if body:
        for p in body.find_all("p"):
            text = p.get_text(strip=True)
            if text:
                paragraphs.append(text)

    return {
        "url": url,
        "title": title,
        "image_url": images,
        "date": date,
        "paragraphs": paragraphs,
    }
